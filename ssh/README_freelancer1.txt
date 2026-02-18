# Complete Guide to Connecting to a Server for Freelancers 1

🚀 Welcome to Project 1!

## Files you received:
1. id_freelancer1 (SSH private key)
2. config_freelancer1 (SSH configuration file)

## Installation and setup steps:

### Step 1: Place the SSH key
In your computer terminal, run:
```bash
# Create the SSH folder if it doesn't exist
mkdir -p ~/.ssh
# Move the key to the SSH folder
mv id_freelancer1 ~/.ssh/

# Set the correct permissions
chmod 600 ~/.ssh/id_freelancer1
```

### Step 2: Set the config file
```bash
# Move the config file
mv config_freelancer1 ~/.ssh/config
# Or if you have a config file, add its contents
cat config_freelancer1 >> ~/.ssh/config
```

### Step 3: Connect to the server
```bash
# Method 1: Using config (easiest)
ssh project1

# Method 2: Direct
ssh -i ~/.ssh/id_freelancer1 freelancer1@62.60.128.97
```

### Step 4: Start working on the project
After connecting to the server:
```bash
# Go to the project folder
cd /var/www/project1

# View files
ls -la

# Create a test file
touch hello.txt
echo "Hello from Freelancer 1" > hello.txt
```

## Important information:
- 🖥️ Server: 62.60.128.97
- 👤 Username: freelancer1
- 📁 Project folder: /var/www/project1
- 🔑 SSH port: 22
- 🔑 Password: amir2468

## Security tips:
- Do not share the private key with anyone
- Files are only accessible in your own project folder
- Access to other project folders You don't have

## In case of problems:
1. Make sure the file permissions are correct: chmod 600 ~/.ssh/id_freelancer1
2. Ask the admin for help

Good luck! 🎉