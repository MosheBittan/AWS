#!/bin/bash
yum update -y
yum install -y httpd
systemctl start httpd
systemctl enable httpd
EC2_AVAIL_ZONE=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)
#script get your browser time each time you refresh and insert to page
echo "<h1>Hello from $(hostname -f) in AZ $EC2_AVAIL_ZONE at <span id='date'></span></h1><script>document.getElementById('date').innerHTML = new Date();</script>" > /var/www/html/index.html
