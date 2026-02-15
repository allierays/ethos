#!/bin/bash
# Rename checklist: ethos -> ethos-academy
# Run each step manually in order. Do NOT run this script directly.

set -euo pipefail

echo "=== Step 1: Rename GitHub repo ==="
echo "Go to: https://github.com/allierays/ethos/settings"
echo "Change 'Repository name' to: ethos-academy"
echo "GitHub auto-redirects the old URL."
echo ""
echo "Press Enter after you've done this..."
read -r

echo "=== Step 2: Update local remote ==="
git remote set-url origin https://github.com/allierays/ethos-academy.git
git remote -v
echo ""

echo "=== Step 3: SSH into EC2 and rename ==="
echo "Run these commands on the server:"
echo ""
echo "  ssh -i your-key.pem ubuntu@YOUR_EC2_IP"
echo ""
echo "  # Rename the directory"
echo "  mv ~/ethos ~/ethos-academy"
echo ""
echo "  # Update the git remote"
echo "  cd ~/ethos-academy"
echo "  git remote set-url origin https://github.com/allierays/ethos-academy.git"
echo "  git remote -v"
echo ""
echo "  # Update cron jobs (they reference ~/ethos)"
echo "  crontab -l | sed 's|/home/ubuntu/ethos|/home/ubuntu/ethos-academy|g' | crontab -"
echo "  crontab -l  # verify"
echo ""
echo "Press Enter after you've done this..."
read -r

echo "=== Step 4: Merge and deploy ==="
echo "Back on your local machine:"
echo ""
echo "  git checkout main"
echo "  git merge rename/ethos-to-ethos-academy"
echo "  git push origin main"
echo ""
echo "The deploy workflow triggers automatically on push to main."
echo ""

echo "=== Step 5: Verify ==="
echo "After deploy completes, check:"
echo "  curl https://api.ethos-academy.com/health"
echo "  curl https://ethos-academy.com"
echo ""
echo "Done."
