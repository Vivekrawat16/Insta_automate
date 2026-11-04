#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
import re
import zipfile
import shutil
import subprocess
from datetime import datetime, timezone

BASE_DIR = '/home/vivek/.gemini/antigravity'
BRAIN_DIR = os.path.join(BASE_DIR, 'brain')
DB_PATH = os.path.join(BASE_DIR, 'conversation_summaries.db')
STATE_FILE = os.path.join(BASE_DIR, 'gdrive_sync_state.json')

PARENT_FOLDER_ID = '1_tRxpwebz8-MI7-vX-cacYXM5-pJsqwD'
RECENT_CHATS_FOLDER_ID = '1DefH92_jXbPYBkHaV2IEOACTcDzQI4Kh'
BRAIN_ZIP_FILE_ID = '1r4k-xlRrKdEW7trEFTad360rjN_rOtXU'
INDEX_FILE_ID = '1DZDVJH_Qiiq_BZs_2P0gT7JXOumQJKnF'

WORK_DIR = '/tmp/antigravity_sync'

def sanitize_filename(name):
    clean = re.sub(r'[^\w\s-]', '', name).strip()
    clean = re.sub(r'[-\s]+', '_', clean)
    return clean[:50] if clean else 'untitled'

def run_cmd(args):
    res = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"Command failed ({' '.join(args)}): {res.stderr.strip()}", file=sys.stderr)
    return res

def get_existing_drive_chats():
    # Return dict of {cid_prefix: file_id} from Recent_Chats folder
    res = run_cmd(['gdrive', 'readonly', 'ls', RECENT_CHATS_FOLDER_ID, '--json'])
    drive_files = {}
    if res.returncode == 0:
        try:
            items = json.loads(res.stdout)
            for item in items:
                name = item.get('name', '')
                fid = item.get('id', '')
                m = re.search(r'_([a-f0-9]{6})\.md$', name)
                if m:
                    drive_files[m.group(1)] = fid
        except Exception as e:
            print(f"Warning: could not parse drive files: {e}", file=sys.stderr)
    return drive_files

def format_conversation_markdown(cid, title, preview, step_count, last_mod, workspaces, conn):
    display_title = title.strip() if title and title.strip() else (preview[:40].strip() or f"Conversation_{cid[:8]}")
    try:
        dt = datetime.fromisoformat(last_mod.replace("Z", "+00:00"))
        nice_date = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        nice_date = str(last_mod)

    lines = []
    lines.append(f"# {display_title}")
    lines.append("")
    lines.append(f"- **Conversation ID:** `{cid}`")
    lines.append(f"- **Date:** {nice_date}")
    lines.append(f"- **Steps:** {step_count}")
    if workspaces:
        lines.append(f"- **Workspace:** `{workspaces}`")
    lines.append("")
    lines.append("---")
    lines.append("")

    transcript_path = os.path.join(BRAIN_DIR, cid, '.system_generated', 'logs', 'transcript.jsonl')
    has_transcript = False
    if os.path.exists(transcript_path):
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                t_lines = f.readlines()

            chat_turns = []
            for t_line in t_lines:
                try:
                    obj = json.loads(t_line)
                    step_type = obj.get('type')
                    if step_type == 'USER_INPUT':
                        content = obj.get('content', '')
                        m = re.search(r'<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>', content, re.DOTALL)
                        if m:
                            content = m.group(1)
                        chat_turns.append(('User', obj.get('created_at', ''), content))
                    elif step_type == 'PLANNER_RESPONSE':
                        content = obj.get('content', '')
                        tool_calls = obj.get('tool_calls', [])
                        t_summary = ""
                        if tool_calls:
                            tools_used = [tc.get('name', 'tool') for tc in tool_calls]
                            t_summary = f"\n*Tools used: {', '.join(tools_used)}*"
                        full_msg = (content or '').strip()
                        if t_summary:
                            full_msg = (full_msg + "\n" + t_summary).strip()
                        if full_msg:
                            chat_turns.append(('Assistant (Antigravity)', obj.get('created_at', ''), full_msg))
                except Exception:
                    continue

            if chat_turns:
                has_transcript = True
                for role, t_time, msg in chat_turns:
                    time_header = f" ({t_time})" if t_time else ""
                    lines.append(f"### {role}{time_header}")
                    lines.append("")
                    lines.append(msg)
                    lines.append("")
                    lines.append("---")
                    lines.append("")
        except Exception as e:
            print(f"Error reading transcript for {cid}: {e}", file=sys.stderr)
            has_transcript = False

    if not has_transcript:
        c = conn.cursor()
        c.execute('''
        SELECT chunk_index, user_body, agent_body
        FROM conversations_fts
        WHERE conversation_id = ?
        ORDER BY chunk_index ASC
        ''', (cid,))
        chunks = c.fetchall()
        if chunks:
            for c_idx, u_body, a_body in chunks:
                if u_body and u_body.strip():
                    lines.append("### User")
                    lines.append("")
                    lines.append(u_body.strip())
                    lines.append("")
                    lines.append("---")
                    lines.append("")
                if a_body and a_body.strip():
                    lines.append("### Assistant (Antigravity)")
                    lines.append("")
                    lines.append(a_body.strip())
                    lines.append("")
                    lines.append("---")
                    lines.append("")
        else:
            lines.append("*(No message body text recorded in index for this conversation)*")
            lines.append("")

    return "\n".join(lines)

def main():
    print(f"[{datetime.now().isoformat()}] Starting Antigravity chats & brain sync to Google Drive...")
    os.makedirs(WORK_DIR, exist_ok=True)
    chats_tmp_dir = os.path.join(WORK_DIR, 'chats')
    os.makedirs(chats_tmp_dir, exist_ok=True)

    # 1. Read last sync state (default to 2026-11-03 14:03:00 which was the initial full backup)
    last_sync_time = "2026-11-03 14:03:00"
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                last_sync_time = state.get('last_sync_time', last_sync_time)
        except Exception as e:
            print(f"Warning: could not read {STATE_FILE}: {e}", file=sys.stderr)

    print(f"Checking for chats modified after: {last_sync_time}")

    # 2. Query conversations from DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
    SELECT conversation_id, title, preview, step_count, last_modified_time, workspace_uris
    FROM conversation_summaries
    WHERE last_modified_time > ?
    ORDER BY last_modified_time DESC
    ''', (last_sync_time,))
    changed_convs = c.fetchall()

    c.execute('SELECT COUNT(*) FROM conversation_summaries')
    total_convs = c.fetchone()[0]

    print(f"Total conversations in Antigravity: {total_convs}")
    print(f"New or modified conversations to sync: {len(changed_convs)}")

    uploaded_count = 0
    updated_count = 0

    if changed_convs:
        existing_drive_chats = get_existing_drive_chats()
        for idx, (cid, title, preview, step_count, last_mod, workspaces) in enumerate(changed_convs):
            display_title = title.strip() if title and title.strip() else (preview[:40].strip() or f"Conversation_{cid[:8]}")
            clean_title = sanitize_filename(display_title)
            cid_prefix = cid[:6]

            try:
                dt = datetime.fromisoformat(last_mod.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d_%H%M")
            except Exception:
                date_str = "unknown_date"

            filename = f"{date_str}_{clean_title}_{cid_prefix}.md"
            filepath = os.path.join(chats_tmp_dir, filename)

            md_content = format_conversation_markdown(cid, title, preview, step_count, last_mod, workspaces, conn)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)

            # Upload or Update in Google Drive
            if cid_prefix in existing_drive_chats:
                file_id = existing_drive_chats[cid_prefix]
                print(f"Updating existing Drive file {file_id} for '{display_title}'...")
                res = run_cmd(['gdrive', 'mutate', 'update', file_id, filepath])
                if res.returncode == 0:
                    updated_count += 1
            else:
                print(f"Uploading new chat '{display_title}' ({filename})...")
                res = run_cmd(['gdrive', 'mutate', 'upload', filepath, '--parent', RECENT_CHATS_FOLDER_ID])
                if res.returncode == 0:
                    uploaded_count += 1

        # 3. Regenerate master INDEX.md
        c.execute('''
        SELECT conversation_id, title, preview, step_count, last_modified_time
        FROM conversation_summaries
        ORDER BY last_modified_time DESC
        ''')
        all_convs = c.fetchall()

        index_path = os.path.join(WORK_DIR, 'INDEX.md')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("# Antigravity Chat Transcripts Index\n\n")
            f.write(f"Total Conversations: **{len(all_convs)}**  \n")
            f.write(f"Last Synced: **{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}**  \n\n")
            f.write("| # | Date (UTC) | Conversation Title | Steps | Conversation ID |\n")
            f.write("|---|---|---|---|---|\n")
            for num, (cid, title, preview, step_count, last_mod) in enumerate(all_convs, 1):
                display_title = title.strip() if title and title.strip() else (preview[:40].strip() or f"Conversation_{cid[:8]}")
                try:
                    dt = datetime.fromisoformat(last_mod.replace("Z", "+00:00"))
                    nice_date = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    nice_date = str(last_mod)[:16]
                f.write(f"| {num} | {nice_date} | {display_title} | {step_count} | `{cid[:8]}...` |\n")

        print("Updating INDEX.md on Google Drive...")
        run_cmd(['gdrive', 'mutate', 'update', INDEX_FILE_ID, index_path])

        # 4. Zip and update antigravity_brain.zip
        brain_zip_path = os.path.join(WORK_DIR, 'antigravity_brain.zip')
        print("Compressing ~/.gemini/antigravity/brain...")
        try:
            with zipfile.ZipFile(brain_zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
                for root, dirs, files in os.walk(BRAIN_DIR):
                    for file in files:
                        full_p = os.path.join(root, file)
                        rel_p = os.path.relpath(full_p, BASE_DIR)
                        z.write(full_p, rel_p)
            print(f"Brain archive created ({os.path.getsize(brain_zip_path) / (1024*1024):.1f} MB). Updating on Google Drive...")
            run_cmd(['gdrive', 'mutate', 'update', BRAIN_ZIP_FILE_ID, brain_zip_path])
        except Exception as e:
            print(f"Error updating brain zip: {e}", file=sys.stderr)

    else:
        print("No new conversations since last sync.")

    # 5. Save sync state
    new_sync_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S+00:00")
    with open(STATE_FILE, 'w') as f:
        json.dump({'last_sync_time': new_sync_time}, f, indent=2)

    # 6. Cleanup
    shutil.rmtree(WORK_DIR, ignore_errors=True)

    print(f"Sync complete! Synced: {uploaded_count} new chats, {updated_count} updated chats. Brain & INDEX updated in Google Drive.")

if __name__ == '__main__':
    main()
