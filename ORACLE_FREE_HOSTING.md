---
noteId: "70a08d3068b711f1adc5e5fbe6051bee"
tags: []

---

# Host CropSmart 24/7 on Oracle Cloud Always Free

Render free web services can sleep when inactive. For an always-on free server, use an Oracle Cloud Always Free VM and run this app as a Linux service.

## 1. Create The Free VM

1. Create an Oracle Cloud Free Tier account.
2. Create an **Always Free** compute instance.
3. Use Ubuntu as the operating system.
4. Open inbound ports in Oracle networking:
   - `22` for SSH
   - `80` for the website
   - `443` if you later add HTTPS

## 2. Upload Your Project

SSH into the VM, then install basic tools:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv nginx
```

Clone your GitHub repository:

```bash
git clone YOUR_GITHUB_REPO_URL cropsmart
cd cropsmart
```

Test the app:

```bash
python3 server.py 8080
```

Open this in the browser to check it:

```text
http://YOUR_SERVER_PUBLIC_IP:8080/
```

Stop the test server with `Ctrl+C`.

## 3. Run The App Always

Create a systemd service:

```bash
sudo nano /etc/systemd/system/cropsmart.service
```

Paste this, replacing `/home/ubuntu/cropsmart` if your folder is different:

```ini
[Unit]
Description=CropSmart crop price app
After=network.target

[Service]
WorkingDirectory=/home/ubuntu/cropsmart
Environment=PORT=8080
Environment=HOST=127.0.0.1
ExecStart=/usr/bin/python3 /home/ubuntu/cropsmart/server.py
Restart=always
RestartSec=5
User=ubuntu

[Install]
WantedBy=multi-user.target
```

Start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cropsmart
sudo systemctl start cropsmart
sudo systemctl status cropsmart
```

## 4. Put Nginx In Front

Create an Nginx config:

```bash
sudo nano /etc/nginx/sites-available/cropsmart
```

Paste this:

```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable it:

```bash
sudo ln -s /etc/nginx/sites-available/cropsmart /etc/nginx/sites-enabled/cropsmart
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

Now open:

```text
http://YOUR_SERVER_PUBLIC_IP/
```

## 5. Optional Domain

In your domain DNS, create an `A` record:

```text
@  -> YOUR_SERVER_PUBLIC_IP
www -> YOUR_SERVER_PUBLIC_IP
```

Then update the Nginx `server_name`:

```nginx
server_name yourdomain.com www.yourdomain.com;
```

For HTTPS:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## Notes

- Oracle Always Free can run 24/7, but Oracle may suspend or terminate idle/free accounts that violate their rules or appear abandoned.
- Keep one VM running and avoid creating paid resources unless you understand the cost.
- This project does not require paid Python dependencies.
