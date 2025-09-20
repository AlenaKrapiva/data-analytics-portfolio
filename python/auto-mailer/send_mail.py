from __future__ import annotations
from pathlib import Path
from datetime import datetime
import os, re, argparse, base64, sys
import pandas as pd
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName, FileType, Disposition
)

# -------- безопасная печать (без Unicode-ошибок в консоли Windows) --------
def cprint(*args):
    s = " ".join(str(a) for a in args)
    try:
        print(s)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or "cp1251"
        print(s.encode(enc, "replace").decode(enc))

# -------- пути --------
MERGE_PATH = Path("data/processed/mail_merge.csv")
SUBJ_TPL   = Path("templates/subject.txt")
BODY_TPL   = Path("templates/body.txt")
ATTACH_DIR = Path("data/attachments")
LOG_PATH   = Path("state/sent_log.csv")

# -------- утилиты --------
def render_template(tpl_text: str, mapping: dict) -> str:
    def repl(m):
        k = m.group(1).strip()
        v = mapping.get(k, "")
        if isinstance(v, float) and v.is_integer():
            v = int(v)
        return str(v) if v is not None else ""
    return re.sub(r"{{\s*([a-zA-Z0-9_]+)\s*}}", repl, tpl_text)

def load_log() -> set[tuple[str, str]]:
    if LOG_PATH.exists():
        try:
            df = pd.read_csv(LOG_PATH, encoding="utf-8")
            if "status" in df.columns:
                df = df[df["status"] == "sent"]   # считаем дублями только успешные отправки
            return set(zip(df.get("email", []), df.get("subject", [])))
        except Exception:
            pass
    return set()

def append_log(email: str, subject: str, status: str, err: str = ""):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = pd.DataFrame([{
        "ts": now, "email": email, "subject": subject, "status": status, "error": err
    }])
    header = not LOG_PATH.exists()
    line.to_csv(LOG_PATH, mode="a", header=header, index=False, encoding="utf-8")

def send_via_sendgrid(to_email: str, subject: str, body: str, attachments: list[str] | None):
    api = os.getenv("SENDGRID_API_KEY")
    if not api:
        raise RuntimeError("Нет SENDGRID_API_KEY в .env")
    from_email = os.getenv("MAIL_FROM") or os.getenv("GMAIL_USER")
    from_name  = os.getenv("MAIL_FROM_NAME", "Auto Mailer")

    msg = Mail(
        from_email=(from_email, from_name),
        to_emails=to_email,
        subject=subject,
        plain_text_content=body,
    )

    if attachments:
        msg.attachments = []
        for p in attachments:
            data = Path(p).read_bytes()
            att = Attachment()
            att.file_content = FileContent(base64.b64encode(data).decode())
            att.file_type    = FileType("application/octet-stream")
            att.file_name    = FileName(Path(p).name)
            att.disposition  = Disposition("attachment")
            msg.attachments.append(att)

    SendGridAPIClient(api).send(msg)

# -------- main --------
def main():
    ap = argparse.ArgumentParser(description="Mail sender")
    ap.add_argument("--send", action="store_true", help="real send emails (not just preview)")
    args = ap.parse_args()

    load_dotenv()

    if not MERGE_PATH.exists():
        raise SystemExit(f"Нет файла {MERGE_PATH}. Сначала запусти prepare_recipients.py")

    df = pd.read_csv(MERGE_PATH, encoding="utf-8")
    if "active" in df.columns:
        df = df[df["active"] == 1]

    subj_tpl = SUBJ_TPL.read_text(encoding="utf-8")
    body_tpl = BODY_TPL.read_text(encoding="utf-8")

    sent_pairs = load_log()
    sent_cnt, skipped_cnt = 0, 0

    for _, row in df.iterrows():
        row_map = {k: ("" if pd.isna(v) else v) for k, v in row.items()}
        to_email = str(row_map.get("email", "")).strip()
        if not to_email:
            continue

        # можно добавить дату запуска, чтобы тема была всегда новая:
        # row_map["run_date"] = datetime.now().strftime("%Y-%m-%d")

        subject = render_template(subj_tpl, row_map)
        body    = render_template(body_tpl, row_map)

        # вложение (опционально): колонка "attachment"
        attachments = None
        att_name = str(row_map.get("attachment", "")).strip()
        if att_name:
            path = ATTACH_DIR / att_name
            if path.exists():
                attachments = [str(path)]
            else:
                cprint(f"[WARN] Attachment not found: {path}")

        pair = (to_email, subject)
        if pair in sent_pairs:
            skipped_cnt += 1
            cprint(f"[SKIP duplicate] {to_email} | {subject}")
            continue

        if args.send:
            try:
                send_via_sendgrid(to_email, subject, body, attachments)
                append_log(to_email, subject, "sent", "")
                cprint(f"[SENT] {to_email} | {subject}")
                sent_cnt += 1
            except Exception as e:
                append_log(to_email, subject, "error", str(e))
                cprint(f"[ERROR] {to_email}: {e}")
        else:
            cprint("----- PREVIEW -----")
            cprint(f"Кому:   {to_email}")
            cprint(f"Тема:   {subject}")
            cprint(f"Тело:\n{body}\n")
            cprint(f"(вложение: {att_name or 'нет'})")
            # предпросмотр не логируем как 'sent', чтобы не блокировать отправку
            sent_cnt += 1

    mode = "SEND" if args.send else "PREVIEW"
    cprint(f"\n[{mode}] Готово. Обработано: {sent_cnt}, пропущено (дубли): {skipped_cnt}. Лог: {LOG_PATH}")

if __name__ == "__main__":
    main()
