def register_blueprints(app):
    from routes.auth import auth_bp
    from routes.fileroom import fileroom_bp
    from routes.binder import binder_bp
    from routes.folder import folder_bp
    from routes.document import document_bp
    from routes.workflow import workflow_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(fileroom_bp)
    app.register_blueprint(binder_bp)
    app.register_blueprint(folder_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(workflow_bp)
    app.register_blueprint(admin_bp)
