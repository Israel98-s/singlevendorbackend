#!/bin/bash

echo "Starting deployment..."

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib nginx

# Create database
sudo -u postgres psql -c "CREATE DATABASE ecommerce_db;"
sudo -u postgres psql -c "CREATE USER ecommerce_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "ALTER ROLE ecommerce_user SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE ecommerce_user SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE ecommerce_user SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ecommerce_db TO ecommerce_user;"

# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create email templates directory
mkdir -p store/templates/emails

# Run migrations and create sample data
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py create_sample_data

# Install and configure Gunicorn
pip install gunicorn
sudo tee /etc/systemd/system/gunicorn.service > /dev/null <<EOF
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/project
ExecStart=/path/to/your/project/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/path/to/your/project/ecommerce.sock ecommerce.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl start gunicorn
sudo systemctl enable gunicorn

echo "Deployment completed!"
echo "Access your API at: http://your-domain/api/"
echo "Swagger docs at: http://your-domain/swagger/"
echo "Admin panel at: http://your-domain/admin/"
echo "Default admin credentials: admin@ecommerce.com / admin123"