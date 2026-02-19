import csv
import io
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "contacts_raw.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


PY2 = sys.version_info[0] == 2


def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def open_csv_read(path):
    if PY2:
        return open(path, "rb")
    return io.open(path, mode="r", encoding="utf-8", newline="")


def open_csv_write(path):
    if PY2:
        return open(path, "wb")
    return io.open(path, mode="w", encoding="utf-8", newline="")


def load_contacts(path):
    if not os.path.exists(path):
        raise IOError("Contacts file not found: {}".format(path))
    with open_csv_read(path) as f:
        return list(csv.DictReader(f))


def normalise_spaces(text):
    """Trim and collapse repeated spaces to a single space."""
    text = (text or "").strip()
    return re.sub(r"\s+", " ", text)


def clean_name(name):
    name = normalise_spaces(name)
    if not name:
        return ""

    words = []
    for word in name.split(" "):
        # Handle hyphenated names: "amy-walker" -> "Amy-Walker"
        parts = [p[:1].upper() + p[1:].lower() if p else "" for p in word.split("-")]
        words.append("-".join(parts))

    return " ".join(words)


def clean_email(email):
    return normalise_spaces(email).lower()


def clean_company(company):
    company = normalise_spaces(company)
    if not company:
        return ""
    # Title Case is fine for a demo (later you could keep Ltd/PLC formatting)
    return company.title()


def clean_phone(phone):
    phone = normalise_spaces(phone)

    # Keep only digits and plus
    phone = re.sub(r"[^\d+]", "", phone)

    if phone.startswith("+44"):
        phone = "0" + phone[3:]  # +44... -> 0...

    # Finally keep only digits
    phone = re.sub(r"\D", "", phone)
    return phone


def clean_contact(row):
    return {
        "name": clean_name(row.get("name", "")),
        "email": clean_email(row.get("email", "")),
        "phone": clean_phone(row.get("phone", "")),
        "company": clean_company(row.get("company", "")),
    }

def is_valid_email(email):
    email = email.strip()
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))

def is_valid_uk_phone(phone):
    # very simple UK-friendly check: must be digits, start with 0, and be 10-11 digits
    return phone.isdigit() and phone.startswith("0") and (10 <= len(phone) <= 11)

def completeness_score(contact):
    """Higher score = keep this record when duplicates exist."""
    score = 0
    for key in ["name", "email", "phone", "company"]:
        if contact.get(key):
            score += 1
    return score

def main():
    ensure_dir(OUTPUT_DIR)

    contacts = load_contacts(DATA_FILE)

    print("CONTACT CLEANER - BEFORE -> AFTER")
    print("-" * 45)
    print("Loaded rows: {}\n".format(len(contacts)))

    cleaned_contacts = []
    stats = {
        "total": 0,
        "missing_name": 0,
        "missing_email": 0,
        "invalid_email": 0,
        "missing_phone": 0,
        "invalid_phone": 0,
        "missing_company": 0,
    }

    for row in contacts:
        stats["total"] += 1
        cleaned = clean_contact(row)
        cleaned_contacts.append(cleaned)

        if not cleaned["name"]:
            stats["missing_name"] += 1
        if not cleaned["email"]:
            stats["missing_email"] += 1
        elif not is_valid_email(cleaned["email"]):
            stats["invalid_email"] += 1

        if not cleaned["phone"]:
            stats["missing_phone"] += 1
        elif not is_valid_uk_phone(cleaned["phone"]):
            stats["invalid_phone"] += 1

        if not cleaned["company"]:
            stats["missing_company"] += 1

    deduped = {}
    duplicates_removed = 0
    for c in cleaned_contacts:
        email = c["email"]

        # If no email, we cannot dedupe reliably; keep as-is using a unique key.
        if not email:
            deduped["NOEMAIL_{}".format(id(c))] = c
            continue

        if email not in deduped:
            deduped[email] = c
        else:
            # Keep the record with more complete info.
            existing = deduped[email]
            if completeness_score(c) > completeness_score(existing):
                deduped[email] = c
            duplicates_removed += 1

    deduped_contacts = list(deduped.values())
    output_csv = os.path.join(OUTPUT_DIR, "cleaned_contacts.csv")

    with open_csv_write(output_csv) as f:
        writer = csv.DictWriter(f, fieldnames=["name", "email", "phone", "company"])
        writer.writeheader()
        writer.writerows(deduped_contacts)
    report_path = os.path.join(OUTPUT_DIR, "cleaning_report.txt")

    with io.open(report_path, "w", encoding="utf-8") as f:
        f.write(u"CLEANING REPORT\n")
        f.write(u"=" * 30 + u"\n")
        f.write(u"total_rows: {}\n".format(stats["total"]))
        f.write(u"rows_after_dedup: {}\n".format(len(deduped_contacts)))
        f.write(u"duplicates_removed: {}\n".format(duplicates_removed))
        for key in ["missing_name", "missing_email", "invalid_email", "missing_phone", "invalid_phone", "missing_company"]:
            f.write(u"{}: {}\n".format(key, stats[key]))

    print("Saved report -> {}".format(report_path))
    print("")
    print("Saved cleaned CSV -> {}".format(output_csv))

    print("duplicates_removed: {}".format(duplicates_removed))
    print("rows_after_dedup: {}".format(len(deduped_contacts)))

    print("CLEANING REPORT")
    print("-" * 20)
    for k, v in stats.items():
        print("{}: {}".format(k, v))


if __name__ == "__main__":
    main()
