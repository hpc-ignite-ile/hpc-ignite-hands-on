# บทที่ 29: Data Security บน HPC

Chapter 29: Data Security

## วัตถุประสงค์การเรียนรู้

1. เข้าใจ HPC Security Best Practices
2. จัดการ SSH Keys และ Credentials
3. ปกป้องข้อมูลวิจัย
4. ปฏิบัติตาม Data Governance

## โครงสร้างไฟล์

```
chapter-29-security/
├── README.md
├── ssh_key_management.sh   # SSH key setup
├── file_permissions.py     # Permission audit
├── secure_transfer.sh      # Secure data transfer
└── credential_vault.py     # Credential management
```

## การใช้งาน

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy to LANTA
ssh-copy-id username@lanta.nstda.or.th

# Check file permissions
python file_permissions.py ~/research_data
```

## Security Checklist

- [ ] Use SSH key authentication (not passwords)
- [ ] Set proper file permissions (chmod 700 for private)
- [ ] Encrypt sensitive data
- [ ] Don't commit credentials to git
- [ ] Use .gitignore for sensitive files

## Copy-paste only บน LANTA

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

บทนี้ยังไม่มี Python script แบบ standalone ในโฟลเดอร์เดียวกัน แต่ผู้เรียนสามารถเปิดเนื้อหาแบบไม่ใช้ editor ได้ด้วย block นี้:

```bash
cat > /tmp/hpc_ignite_ai-applications-chapter-29-security.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

echo "อ่าน lab: ai-applications/chapter-29-security"
echo "ไฟล์ในบทนี้:"
find "ai-applications/chapter-29-security" -maxdepth 1 -type f | sort
echo
echo "README preview:"
sed -n '1,180p' "ai-applications/chapter-29-security/README.md"
echo
echo "ถ้าจะเพิ่ม runnable Slurm lab ให้ใช้ template: docs/LAB_AUTHORING_GUIDE_TH.md"
BASH

bash /tmp/hpc_ignite_ai-applications-chapter-29-security.sh
```
