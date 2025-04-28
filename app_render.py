# app_render.py (trecho do create_app)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    # Registra os blueprints
    from routes_nd import nd
    from routes_item import item_bp

    app.register_blueprint(nd)
    app.register_blueprint(item_bp)

    app.register_blueprint(main)

    with app.app_context():
        db.create_all()

        # Corrige colunas se necessário
        try:
            db.session.execute(text('ALTER TABLE natureza_despesa ADD COLUMN descricao VARCHAR(255);'))
            db.session.commit()
            print("Coluna 'descricao' adicionada na tabela natureza_despesa!")
        except Exception as e:
            db.session.rollback()
            print(f"(INFO) Coluna 'descricao' pode já existir: {e}")

        try:
            db.session.execute(text('ALTER TABLE natureza_despesa ADD COLUMN numero VARCHAR(50);'))
            db.session.commit()
            print("Coluna 'numero' adicionada na tabela natureza_despesa!")
        except Exception as e:
            db.session.rollback()
            print(f"(INFO) Coluna 'numero' pode já existir: {e}")

        try:
            db.session.execute(text('ALTER TABLE usuario ADD COLUMN matricula VARCHAR(50);'))
            db.session.commit()
            print("Coluna 'matricula' adicionada na tabela usuario!")
        except Exception as e:
            db.session.rollback()
            print(f"(INFO) Coluna 'matricula' pode já existir: {e}")

        try:
            db.session.execute(text('ALTER TABLE item ADD COLUMN codigo VARCHAR(50);'))
            db.session.execute(text('ALTER TABLE item ADD COLUMN nome VARCHAR(255);'))
            db.session.execute(text('ALTER TABLE item ADD COLUMN nd_id INTEGER;'))
            db.session.commit()
            print("Tabela 'item' corrigida!")
        except Exception as e:
            db.session.rollback()
            print(f"(INFO) Tabela 'item' pode já estar corrigida: {e}")

        # Cria perfil ADMIN se não existir
        perfil_admin = Perfil.query.filter_by(nome='Admin').first()
        if not perfil_admin:
            perfil_admin = Perfil(nome='Admin')
            db.session.add(perfil_admin)
            db.session.commit()

        # Cria usuário ADMIN se não existir
        admin_email = "admin@admin.com"
        if not Usuario.query.filter_by(email=admin_email).first():
            usuario_admin = Usuario(
                nome="Administrador",
                email=admin_email,
                senha=generate_password_hash("admin123"),
                perfil_id=perfil_admin.id,
                matricula="0001"
            )
            db.session.add(usuario_admin)
            db.session.commit()

    return app
