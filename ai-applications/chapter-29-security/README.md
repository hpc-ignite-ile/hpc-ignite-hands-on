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

บทนี้เป็นแนวคิดหรือ configuration เป็นหลัก จึงไม่มี Python script ขนาดเล็กให้ส่งทันที ใช้ template ใน `docs/LAB_AUTHORING_GUIDE_TH.md` เพื่อสร้าง `src/*.py` และ `jobs/*.sbatch` ด้วย heredoc แล้วส่งด้วย `sbatch` โดยตรง
