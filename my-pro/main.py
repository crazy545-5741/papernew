from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_mail import Mail, Message
import json
import os
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import base64

app = Flask(__name__)
app.secret_key = 'trustpaper_secret_key_2024'

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('GMAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('GMAIL_APP_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('GMAIL_USERNAME')

mail = Mail(app)

# File to store user data and admin notifications
USERS_FILE = 'users.json'
NOTIFICATIONS_FILE = 'notifications.json'

def load_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return []

def save_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def send_email(to_email, subject, body):
    """Send email notification"""
    try:
        msg = Message(subject=subject, recipients=[to_email], body=body)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def verify_school_online(school_name):
    """Simple school verification - you can enhance this with actual APIs"""
    # For demo purposes, we'll accept schools with common keywords
    common_school_keywords = ['school', 'high', 'academy', 'college', 'university', 'institute', 'education']
    school_lower = school_name.lower()
    return any(keyword in school_lower for keyword in common_school_keywords)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/signin')
def signin():
    return render_template('signin.html')

@app.route('/submit_signup', methods=['POST'])
def submit_signup():
    name = request.form['name']
    email = request.form['email']
    class_name = request.form['class']
    roll_no = request.form['roll_no']
    school = request.form['school']
    marks = request.form['marks']
    password = request.form['password']

    # Verify school
    if verify_school_online(school):
        # Save user data
        users = load_data(USERS_FILE)
        user_data = {
            'name': name,
            'email': email,
            'class': class_name,
            'roll_no': roll_no,
            'school': school,
            'marks': marks,
            'password': password,
            'status': 'pending',
            'signup_date': datetime.now().isoformat(),
            'unit_marks': {}
        }
        users.append(user_data)
        save_data(USERS_FILE, users)

        # Add to admin notifications
        notifications = load_data(NOTIFICATIONS_FILE)
        notification = {
            'type': 'signup_request',
            'user': user_data,
            'id': len(notifications) + 1,
            'timestamp': datetime.now().isoformat()
        }
        notifications.append(notification)
        save_data(NOTIFICATIONS_FILE, notifications)

        flash('Sign up successful! Please wait for admin approval to sign in.', 'success')
        return redirect(url_for('signin'))
    else:
        flash('Unable to sign up. Please recheck your school information and try again.', 'error')
        return redirect(url_for('signup'))

@app.route('/admin')
def admin_dashboard():
    notifications = load_data(NOTIFICATIONS_FILE)
    users = load_data(USERS_FILE)
    total_students = len([user for user in users if user.get('status') == 'approved'])
    return render_template('admin.html', notifications=notifications, total_students=total_students)

@app.route('/signin_submit', methods=['POST'])
def signin_submit():
    name = request.form['name']
    password = request.form['password']

    users = load_data(USERS_FILE)
    for user in users:
        if user['name'] == name and user.get('password') == password:
            if user.get('status') == 'approved':
                session['user_id'] = user['name']
                session['user_data'] = user
                flash('Sign in successful!', 'success')
                return redirect(url_for('student_dashboard'))
            else:
                flash('Your account is still pending approval.', 'error')
                return redirect(url_for('signin'))

    flash('Invalid credentials or account not found.', 'error')
    return redirect(url_for('signin'))

@app.route('/student_dashboard')
def student_dashboard():
    if 'user_id' not in session:
        flash('Please sign in first.', 'error')
        return redirect(url_for('signin'))

    user_data = session.get('user_data')
    return render_template('student_dashboard.html', user=user_data)

@app.route('/template_gallery')
def template_gallery():
    if 'user_id' not in session:
        flash('Please sign in first.', 'error')
        return redirect(url_for('signin'))

    # Load user's custom designs
    users = load_data(USERS_FILE)
    user_name = session['user_id']
    custom_designs = []
    
    for user in users:
        if user['name'] == user_name:
            custom_designs = user.get('custom_designs', [])
            break

    return render_template('template_gallery.html', custom_designs=custom_designs)

@app.route('/update_marks', methods=['POST'])
def update_marks():
    if 'user_id' not in session:
        return redirect(url_for('signin'))

    users = load_data(USERS_FILE)
    user_name = session['user_id']

    # Get unit marks from form
    unit_marks = {}
    for key in request.form:
        if key.startswith('unit_'):
            unit_marks[key] = request.form[key]

    # Update user's unit marks
    for user in users:
        if user['name'] == user_name:
            user['unit_marks'] = unit_marks
            session['user_data'] = user
            break

    save_data(USERS_FILE, users)
    flash('Marks updated successfully!', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/generate_ai_design', methods=['POST'])
def generate_ai_design():
    if 'user_id' not in session:
        flash('Please sign in first.', 'error')
        return redirect(url_for('signin'))

    # Get form data
    design_description = request.form.get('design_description', '')
    style_preference = request.form.get('style_preference', 'modern')
    color_mood = request.form.get('color_mood', 'vibrant')

    if not design_description.strip():
        flash('Please provide a description for your certificate design.', 'error')
        return redirect(url_for('template_gallery'))

    # Generate AI design data (simulated)
    design_name = f"ai_design_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    display_name = f"AI Design {datetime.now().strftime('%H:%M')}"
    
    # Create color palette based on mood
    color_palettes = {
        'vibrant': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'],
        'pastel': ['#FFB3BA', '#BAFFC9', '#BAE1FF', '#FFFFBA', '#FFDFBA'],
        'monochrome': ['#2C3E50', '#34495E', '#7F8C8D', '#BDC3C7', '#ECF0F1'],
        'gradient': ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe'],
        'neon': ['#00FFF0', '#FF00FF', '#00FF00', '#FFFF00', '#FF0080'],
        'earthy': ['#8B4513', '#A0522D', '#CD853F', '#DEB887', '#F4A460']
    }
    
    # Create the custom design object
    custom_design = {
        'name': design_name,
        'display_name': display_name,
        'description': design_description,
        'style_preference': style_preference,
        'color_mood': color_mood,
        'color_palette': color_palettes.get(color_mood, color_palettes['vibrant']),
        'created_at': datetime.now().isoformat()
    }

    # Save to user's custom designs
    users = load_data(USERS_FILE)
    user_name = session['user_id']
    
    for user in users:
        if user['name'] == user_name:
            if 'custom_designs' not in user:
                user['custom_designs'] = []
            user['custom_designs'].append(custom_design)
            session['user_data'] = user
            break

    save_data(USERS_FILE, users)
    flash(f'🎨 AI Design "{display_name}" created successfully!', 'success')
    return redirect(url_for('template_gallery'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

def create_certificate(student_name, school_name, class_name, unit_marks, template='classic', custom_design=None):
    # Create high-resolution certificate image (1800x1200 pixels for better quality)
    width, height = 1800, 1200
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Template-specific color palettes
    if template == 'classic':
        # Enhanced color palette (existing)
        gold_color = '#FFD700'
        dark_gold = '#B8860B'
        royal_blue = '#1e3a8a'
        navy_blue = '#0f1419'
        accent_blue = '#3b82f6'
        gray_color = '#374151'
        light_gray = '#f8f9fa'
        bg_gradient_start = (255, 255, 255)
        bg_gradient_end = (240, 245, 255)
    elif template == 'modern':
        # Modern template colors
        gold_color = '#F59E0B'
        dark_gold = '#D97706'
        royal_blue = '#3B82F6'
        navy_blue = '#1E40AF'
        accent_blue = '#60A5FA'
        gray_color = '#4B5563'
        light_gray = '#F3F4F6'
        bg_gradient_start = (249, 250, 251)
        bg_gradient_end = (243, 244, 246)
    elif template == 'elegant':
        # Elegant template colors
        gold_color = '#B45309'
        dark_gold = '#92400E'
        royal_blue = '#7C2D12'
        navy_blue = '#451A03'
        accent_blue = '#A16207'
        gray_color = '#57534E'
        light_gray = '#FEF7ED'
        bg_gradient_start = (254, 252, 232)
        bg_gradient_end = (251, 246, 232)
    elif template == 'custom' and custom_design:
        # AI Custom design colors
        palette = custom_design.get('color_palette', ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe'])
        gold_color = palette[0] if len(palette) > 0 else '#667eea'
        dark_gold = palette[1] if len(palette) > 1 else '#764ba2'
        royal_blue = palette[2] if len(palette) > 2 else '#f093fb'
        navy_blue = palette[3] if len(palette) > 3 else '#f5576c'
        accent_blue = palette[4] if len(palette) > 4 else '#4facfe'
        gray_color = '#374151'
        light_gray = '#f8f9fa'
        # Convert hex to RGB for gradient
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        bg_gradient_start = hex_to_rgb(palette[0]) if len(palette) > 0 else (102, 126, 234)
        bg_gradient_end = hex_to_rgb(palette[1]) if len(palette) > 1 else (118, 75, 162)
        # Make gradient lighter
        bg_gradient_start = tuple(min(255, c + 100) for c in bg_gradient_start)
        bg_gradient_end = tuple(min(255, c + 120) for c in bg_gradient_end)
    else:  # vibrant
        # Vibrant template colors
        gold_color = '#EAB308'
        dark_gold = '#CA8A04'
        royal_blue = '#7C3AED'
        navy_blue = '#5B21B6'
        accent_blue = '#8B5CF6'
        gray_color = '#6B7280'
        light_gray = '#F5F3FF'
        bg_gradient_start = (245, 243, 255)
        bg_gradient_end = (237, 233, 254)


    # Create gradient background effect based on template
    for y in range(height):
        ratio = y / height
        r = int(bg_gradient_start[0] + (bg_gradient_end[0] - bg_gradient_start[0]) * ratio)
        g = int(bg_gradient_start[1] + (bg_gradient_end[1] - bg_gradient_start[1]) * ratio)
        b = int(bg_gradient_start[2] + (bg_gradient_end[2] - bg_gradient_start[2]) * ratio)
        color = (r, g, b)
        draw.line([(0, y), (width, y)], fill=color)

    # Draw ornate border design
    border_width = 20
    # Outer border
    draw.rectangle([0, 0, width, height], outline=gold_color, width=border_width)
    # Inner decorative border
    inner_margin = 40
    draw.rectangle([inner_margin, inner_margin, width-inner_margin, height-inner_margin], 
                   outline=dark_gold, width=8)

    # Add corner decorations
    corner_size = 80
    for corner_x, corner_y in [(inner_margin, inner_margin), (width-inner_margin-corner_size, inner_margin),
                               (inner_margin, height-inner_margin-corner_size), (width-inner_margin-corner_size, height-inner_margin-corner_size)]:
        # Draw decorative corners
        draw.rectangle([corner_x, corner_y, corner_x+corner_size, corner_y+corner_size], 
                       outline=gold_color, width=4)
        # Inner corner decoration
        draw.rectangle([corner_x+15, corner_y+15, corner_x+corner_size-15, corner_y+corner_size-15], 
                       outline=dark_gold, width=2)

    # Enhanced font loading with better fallbacks
    def load_font(size, weight='normal'):
        font_paths = [
            f"/System/Library/Fonts/Times.ttc",
            f"/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            f"/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            "arial.ttf", "times.ttf"
        ]

        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except (OSError, IOError):
                continue
        return ImageFont.load_default()

    # Load fonts with different sizes
    title_font = load_font(72)
    subtitle_font = load_font(36)
    header_font = load_font(28)
    body_font = load_font(24)
    name_font = load_font(48)
    small_font = load_font(20)

    # Enhanced logo section
    logo_bg_rect = [60, 60, 400, 140]
    draw.rectangle(logo_bg_rect, fill=royal_blue, outline=gold_color, width=3)
    draw.text((80, 85), "TRUST PAPER", fill='white', font=header_font)
    draw.text((80, 115), "Certificate Authority", fill=light_gray, font=small_font)

    # Main title with shadow effect
    title_text = "CERTIFICATE"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2

    # Shadow effect
    draw.text((title_x + 3, 183), title_text, fill=gray_color, font=title_font)
    # Main title
    draw.text((title_x, 180), title_text, fill=royal_blue, font=title_font)

    # Subtitle with better spacing
    subtitle_text = "OF ACADEMIC EXCELLENCE"
    subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (width - subtitle_width) // 2
    draw.text((subtitle_x, 260), subtitle_text, fill=accent_blue, font=subtitle_font)

    # Decorative line under subtitle
    line_y = 310
    line_start = subtitle_x
    line_end = subtitle_x + subtitle_width
    draw.rectangle([line_start, line_y, line_end, line_y + 4], fill=gold_color)

    # Presented to section
    presented_text = "THIS CERTIFICATE IS PROUDLY PRESENTED TO"
    presented_bbox = draw.textbbox((0, 0), presented_text, font=body_font)
    presented_width = presented_bbox[2] - presented_bbox[0]
    presented_x = (width - presented_width) // 2
    draw.text((presented_x, 360), presented_text, fill=gray_color, font=body_font)

    # Student name with enhanced styling
    name_bbox = draw.textbbox((0, 0), student_name.upper(), font=name_font)
    name_width = name_bbox[2] - name_bbox[0]
    name_x = (width - name_width) // 2

    # Name background
    name_bg_padding = 20
    draw.rectangle([name_x - name_bg_padding, 405, name_x + name_width + name_bg_padding, 465], 
                   fill=light_gray, outline=gold_color, width=2)
    draw.text((name_x, 415), student_name.upper(), fill=navy_blue, font=name_font)

    # Calculate performance metrics
    total_marks = 0
    units_count = 0
    highest_mark = 0
    unit_details = []

    for unit, marks in unit_marks.items():
        if marks and str(marks).strip():
            try:
                mark_value = float(marks)
                total_marks += mark_value
                units_count += 1
                highest_mark = max(highest_mark, mark_value)
                unit_details.append(f"{unit.replace('_', ' ').title()}: {mark_value}%")
            except ValueError:
                pass

    average_marks = total_marks / units_count if units_count > 0 else 0

    # Performance grade calculation
    if average_marks >= 90:
        grade = "OUTSTANDING"
        grade_color = gold_color
    elif average_marks >= 80:
        grade = "EXCELLENT" 
        grade_color = accent_blue
    elif average_marks >= 70:
        grade = "GOOD"
        grade_color = royal_blue
    else:
        grade = "SATISFACTORY"
        grade_color = gray_color

    # Achievement text with better formatting
    achievement_lines = [
        "In recognition of exceptional academic performance and dedication",
        f"in {class_name} studies at {school_name}",
        f"Achieving an overall average of {average_marks:.1f}% with grade: {grade}",
        f"Awarded on {datetime.now().strftime('%B %d, %Y')}"
    ]

    start_y = 520
    for i, text in enumerate(achievement_lines):
        text_bbox = draw.textbbox((0, 0), text, font=body_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (width - text_width) // 2

        if i == 2:  # Grade line - highlight it
            draw.text((text_x, start_y + i * 35), text, fill=grade_color, font=body_font)
        else:
            draw.text((text_x, start_y + i * 35), text, fill=gray_color, font=body_font)

    # Detailed marks section
    marks_y = 680
    marks_title = "DETAILED PERFORMANCE:"
    marks_title_bbox = draw.textbbox((0, 0), marks_title, font=header_font)
    marks_title_width = marks_title_bbox[2] - marks_title_bbox[0]
    marks_title_x = (width - marks_title_width) // 2
    draw.text((marks_title_x, marks_y), marks_title, fill=royal_blue, font=header_font)

    # Display unit marks in columns
    if unit_details:
        cols = 2
        col_width = 400
        start_x = (width - (cols * col_width)) // 2

        for i, detail in enumerate(unit_details):
            col = i % cols
            row = i // cols
            x = start_x + col * col_width
            y = marks_y + 50 + row * 30
            draw.text((x, y), detail, fill=gray_color, font=small_font)

    # Enhanced signature section
    sig_section_y = height - 200

    # Signature box
    sig_box = [width - 350, sig_section_y, width - 50, sig_section_y + 120]
    draw.rectangle(sig_box, outline=gold_color, width=2)

    # Authority signature
    draw.text((width - 330, sig_section_y + 20), "Authorized Signature", fill=gray_color, font=small_font)
    draw.rectangle([width - 330, sig_section_y + 50, width - 120, sig_section_y + 53], fill=gray_color)
    draw.text((width - 330, sig_section_y + 65), "ADMIN", fill=royal_blue, font=header_font)
    draw.text((width - 330, sig_section_y + 95), "Trust Paper Academy", fill=gray_color, font=small_font)

    # Enhanced seal design
    seal_center_x = width - 200
    seal_center_y = 280
    seal_radius = 80

    # Multiple concentric circles for better seal effect
    for i, radius in enumerate([seal_radius, seal_radius-15, seal_radius-30]):
        width_val = 6 - i * 2
        color = gold_color if i % 2 == 0 else dark_gold
        draw.ellipse([seal_center_x - radius, seal_center_y - radius,
                      seal_center_x + radius, seal_center_y + radius], 
                     outline=color, width=width_val)

    # Seal text
    draw.text((seal_center_x - 35, seal_center_y - 15), "OFFICIAL", fill=gold_color, font=small_font)
    draw.text((seal_center_x - 25, seal_center_y + 5), "SEAL", fill=gold_color, font=small_font)

    # Add watermark
    watermark_text = "TrustPaper Certified"
    watermark_font = load_font(60)
    watermark_bbox = draw.textbbox((0, 0), watermark_text, font=watermark_font)
    watermark_width = watermark_bbox[2] - watermark_bbox[0]

    # Create semi-transparent watermark effect
    watermark_img = Image.new('RGBA', (watermark_width + 40, 80), (255, 255, 255, 0))
    watermark_draw = ImageDraw.Draw(watermark_img)
    watermark_draw.text((20, 10), watermark_text, fill=(200, 200, 200, 50), font=watermark_font)

    # Rotate and paste watermark
    rotated_watermark = watermark_img.rotate(45, expand=1)
    img.paste(rotated_watermark, (width//2 - rotated_watermark.width//2, height//2 - rotated_watermark.height//2), rotated_watermark)

    return img

@app.route('/preview_certificate', methods=['POST'])
def preview_certificate():
    if 'user_id' not in session:
        return redirect(url_for('signin'))

    user_data = session.get('user_data')
    template = request.form.get('template', 'classic')
    custom_design_name = request.form.get('custom_design')
    custom_design = None

    # Check if it's a custom AI design
    if custom_design_name and custom_design_name.startswith('ai_design_'):
        for design in user_data.get('custom_designs', []):
            if design['name'] == custom_design_name:
                custom_design = design
                template = 'custom'
                break

    if not user_data.get('unit_marks'):
        flash('Please enter your unit marks first before generating certificate.', 'error')
        return redirect(url_for('student_dashboard'))

    # Generate certificate
    certificate_img = create_certificate(
        user_data['name'],
        user_data['school'],
        user_data['class'],
        user_data['unit_marks'],
        template,
        custom_design
    )

    # Save to memory and convert to base64 for preview
    img_io = io.BytesIO()
    certificate_img.save(img_io, 'PNG', quality=95)
    img_io.seek(0)

    # Convert to base64 for display
    img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

    return render_template('certificate_preview.html', 
                         certificate_data=img_base64,
                         template=template,
                         user=user_data)

@app.route('/download_certificate', methods=['POST'])
def download_certificate():
    if 'user_id' not in session:
        return redirect(url_for('signin'))

    user_data = session.get('user_data')
    template = request.form.get('template', 'classic')
    custom_design_name = request.form.get('custom_design')
    custom_design = None

    # Check if it's a custom AI design
    if custom_design_name and custom_design_name.startswith('ai_design_'):
        for design in user_data.get('custom_designs', []):
            if design['name'] == custom_design_name:
                custom_design = design
                template = 'custom'
                break

    if not user_data.get('unit_marks'):
        flash('Please enter your unit marks first before generating certificate.', 'error')
        return redirect(url_for('student_dashboard'))

    # Generate certificate
    certificate_img = create_certificate(
        user_data['name'],
        user_data['school'],
        user_data['class'],
        user_data['unit_marks'],
        template,
        custom_design
    )

    # Save to memory
    img_io = io.BytesIO()
    certificate_img.save(img_io, 'PNG', quality=95)
    img_io.seek(0)

    # Create filename
    filename = f"certificate_{user_data['name'].replace(' ', '_')}_{template}_{datetime.now().strftime('%Y%m%d')}.png"

    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=filename)

@app.route('/admin/approve/<int:notification_id>')
def approve_user(notification_id):
    notifications = load_data(NOTIFICATIONS_FILE)
    users = load_data(USERS_FILE)

    user_email = None
    user_name = None

    for notification in notifications:
        if notification['id'] == notification_id:
            # Update user status
            for user in users:
                if (user['name'] == notification['user']['name'] and 
                    user['roll_no'] == notification['user']['roll_no']):
                    user['status'] = 'approved'
                    user_email = user.get('email')  # Use .get() to avoid KeyError
                    user_name = user['name']
                    break
            # Remove notification
            notifications.remove(notification)
            break

    save_data(NOTIFICATIONS_FILE, notifications)
    save_data(USERS_FILE, users)

    # Send approval email
    if user_email:
        subject = "✅ Account Approved - TrustPaper"
        body = f"""Dear {user_name},

Congratulations! Your account has been approved by the admin.

You can now sign in to TrustPaper using your credentials.

Click here to sign in: {request.url_root}signin

Welcome to TrustPaper - Your Certificate Making Platform!

Best regards,
TrustPaper Team"""

        if send_email(user_email, subject, body):
            flash('User approved successfully! Approval email sent.', 'success')
        else:
            flash('User approved successfully! (Email notification failed)', 'success')
    else:
        flash('User approved successfully! (No email available for notification)', 'success')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/students')
def view_all_students():
    users = load_data(USERS_FILE)
    approved_students = [user for user in users if user.get('status') == 'approved']
    pending_students = [user for user in users if user.get('status') == 'pending']

    return render_template('student_list.html', 
                         approved_students=approved_students,
                         pending_students=pending_students,
                         total_approved=len(approved_students),
                         total_pending=len(pending_students))

@app.route('/admin/remove_student/<student_name>/<roll_no>')
def remove_student(student_name, roll_no):
    users = load_data(USERS_FILE)
    notifications = load_data(NOTIFICATIONS_FILE)

    student_removed = False
    student_email = None

    # Remove from users
    for user in users[:]:  # Create a copy to iterate safely
        if user['name'] == student_name and user['roll_no'] == roll_no:
            student_email = user.get('email')
            users.remove(user)
            student_removed = True
            break

    # Remove from notifications if exists
    for notification in notifications[:]:
        if (notification.get('type') == 'signup_request' and 
            notification['user']['name'] == student_name and 
            notification['user']['roll_no'] == roll_no):
            notifications.remove(notification)
            break

    if student_removed:
        save_data(USERS_FILE, users)
        save_data(NOTIFICATIONS_FILE, notifications)

        # Send removal notification email
        if student_email:
            subject = "Account Removed - TrustPaper"
            body = f"""Dear {student_name},

Your account has been removed from TrustPaper by the administrator.

If you wish to continue using TrustPaper, you will need to sign up again with valid information.

For any questions regarding this action, please contact the administrator.

Best regards,
TrustPaper Team"""

            if send_email(student_email, subject, body):
                flash(f'Student {student_name} removed successfully! Notification email sent.', 'success')
            else:
                flash(f'Student {student_name} removed successfully! (Email notification failed)', 'success')
        else:
            flash(f'Student {student_name} removed successfully!', 'success')
    else:
        flash('Student not found!', 'error')

    return redirect(url_for('view_all_students'))

@app.route('/admin/reject/<int:notification_id>')
def reject_user(notification_id):
    notifications = load_data(NOTIFICATIONS_FILE)
    users = load_data(USERS_FILE)

    user_email = None
    user_name = None
    user_to_remove = None

    for notification in notifications:
        if notification['id'] == notification_id:
            # Find and remove user data
            for user in users:
                if (user['name'] == notification['user']['name'] and 
                    user['roll_no'] == notification['user']['roll_no']):
                    user_email = user.get('email')  # Use .get() to avoid KeyError
                    user_name = user['name']
                    user_to_remove = user
                    break

            # Remove user from users list
            if user_to_remove:
                users.remove(user_to_remove)

            # Remove notification
            notifications.remove(notification)
            break

    save_data(NOTIFICATIONS_FILE, notifications)
    save_data(USERS_FILE, users)

    # Send rejection email
    if user_email:
        subject = "❌ Account Application Update - TrustPaper"
        body = f"""Dear {user_name},

We regret to inform you that your account application has been rejected by our admin team.

This could be due to:
- Incomplete or incorrect information provided
- School verification issues
- Other administrative reasons

You may try signing up again with correct information if you believe this was an error.

For any questions, please contact our support team.

Best regards,
TrustPaper Team"""

        if send_email(user_email, subject, body):
            flash('User rejected! Rejection email sent.', 'info')
        else:
            flash('User rejected! (Email notification failed)', 'info')
    else:
        flash('User rejected! (No email available for notification)', 'info')

    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)