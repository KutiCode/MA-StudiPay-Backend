def init_app(app):
    from app.routes.user_routes import user_bp
    app.register_blueprint(user_bp)

    # Neuen Bank-Blueprint registrieren:
    from app.routes.bank_routes import bank_bp
    app.register_blueprint(bank_bp)