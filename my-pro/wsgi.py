wsgi_content = textwrap.dedent("""\
    # wsgi.py — WSGI entrypoint for hosting (gunicorn)
    # It imports the `app` object from main.py (your original file).
    try:
        from main import app as application
    except Exception:
        # fallback if main.py renamed — try app.py
        from app import create_app
        application = create_app()
""")
with open(os.path.join(dst_dir, "wsgi.py"), "w", encoding="utf-8") as f:
    f.write(wsgi_content)