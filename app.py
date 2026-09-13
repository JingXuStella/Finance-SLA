import os
from datetime import datetime
from decimal import Decimal

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash


def database_url():
    url = os.getenv("DATABASE_URL", "sqlite:///finance.db")
    # Render supplies the legacy postgres:// scheme on some services.
    return url.replace("postgres://", "postgresql://", 1) if url.startswith("postgres://") else url


app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "change-this-before-production"),
    SQLALCHEMY_DATABASE_URI=database_url(),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    client = db.Column(db.String(160), default="")
    manager = db.Column(db.String(80), default="")
    contract_amount = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    subcontract_amount = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    other_cost = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    invoice_amount = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    invoice_status = db.Column(db.String(30), default="未开票", nullable=False)
    notes = db.Column(db.Text, default="")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.String(64), default="")

    @property
    def gross_profit(self):
        return (self.contract_amount or 0) - (self.subcontract_amount or 0) - (self.other_cost or 0)

    @property
    def gross_margin(self):
        return (self.gross_profit / self.contract_amount * 100) if self.contract_amount else 0


def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None


def login_required(view):
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("请先登录。", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    wrapped.__name__ = view.__name__
    return wrapped


def admin_required(view):
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or not user.is_admin:
            flash("此操作仅限管理员。", "danger")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)
    wrapped.__name__ = view.__name__
    return wrapped


def money(value):
    try:
        return Decimal(request.form.get(value, "0") or "0")
    except Exception:
        raise ValueError("金额格式不正确，请输入数字。")


@app.context_processor
def common_context():
    return {"current_user": current_user(), "now_year": datetime.now().year}


@app.template_filter("currency")
def currency(value):
    return f"¥{(value or 0):,.2f}"


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        user = User.query.filter_by(username=request.form.get("username", "").strip()).first()
        if user and user.check_password(request.form.get("password", "")):
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        flash("用户名或密码不正确。", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    selected_year = request.args.get("year", type=int)
    query = Project.query
    if selected_year:
        query = query.filter_by(year=selected_year)
    projects = query.order_by(Project.year.desc(), Project.updated_at.desc()).all()
    totals = {
        "contract": sum((p.contract_amount or 0) for p in projects),
        "subcontract": sum((p.subcontract_amount or 0) for p in projects),
        "invoice": sum((p.invoice_amount or 0) for p in projects),
        "profit": sum((p.gross_profit or 0) for p in projects),
    }
    years = [y[0] for y in db.session.query(Project.year).distinct().order_by(Project.year.desc()).all()]
    return render_template("dashboard.html", projects=projects, years=years, selected_year=selected_year, totals=totals)


@app.route("/projects/new", methods=["GET", "POST"])
@login_required
def project_new():
    if request.method == "POST":
        try:
            project = Project(
                year=int(request.form["year"]), name=request.form["name"].strip(), client=request.form.get("client", "").strip(),
                manager=request.form.get("manager", "").strip(), contract_amount=money("contract_amount"),
                subcontract_amount=money("subcontract_amount"), other_cost=money("other_cost"), invoice_amount=money("invoice_amount"),
                invoice_status=request.form.get("invoice_status", "未开票"), notes=request.form.get("notes", "").strip(),
                created_by=current_user().username,
            )
            if not project.name:
                raise ValueError("项目名称不能为空。")
            db.session.add(project); db.session.commit()
            flash("项目已新增。", "success")
            return redirect(url_for("dashboard"))
        except (ValueError, KeyError) as e:
            flash(str(e), "danger")
    return render_template("project_form.html", project=None)


@app.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
def project_edit(project_id):
    project = db.get_or_404(Project, project_id)
    if request.method == "POST":
        try:
            project.year = int(request.form["year"]); project.name = request.form["name"].strip()
            project.client = request.form.get("client", "").strip(); project.manager = request.form.get("manager", "").strip()
            project.contract_amount = money("contract_amount"); project.subcontract_amount = money("subcontract_amount")
            project.other_cost = money("other_cost"); project.invoice_amount = money("invoice_amount")
            project.invoice_status = request.form.get("invoice_status", "未开票"); project.notes = request.form.get("notes", "").strip()
            if not project.name: raise ValueError("项目名称不能为空。")
            db.session.commit(); flash("项目已更新。", "success")
            return redirect(url_for("dashboard"))
        except (ValueError, KeyError) as e:
            flash(str(e), "danger")
    return render_template("project_form.html", project=project)


@app.route("/projects/<int:project_id>/delete", methods=["POST"])
@admin_required
def project_delete(project_id):
    project = db.get_or_404(Project, project_id)
    db.session.delete(project); db.session.commit()
    flash("项目已删除。", "success")
    return redirect(url_for("dashboard"))


@app.route("/users", methods=["GET", "POST"])
@admin_required
def users():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if len(username) < 2 or len(password) < 8:
            flash("用户名至少 2 位，密码至少 8 位。", "danger")
        elif User.query.filter_by(username=username).first():
            flash("该用户名已经存在。", "danger")
        else:
            user = User(username=username, is_admin=request.form.get("is_admin") == "on")
            user.set_password(password); db.session.add(user); db.session.commit()
            flash("用户已创建。", "success")
            return redirect(url_for("users"))
    return render_template("users.html", users=User.query.order_by(User.created_at.desc()).all())


@app.route("/users/<int:user_id>/toggle", methods=["POST"])
@admin_required
def user_toggle(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user().id:
        flash("不能修改自己的管理员权限。", "warning")
    else:
        user.is_admin = not user.is_admin; db.session.commit(); flash("用户权限已更新。", "success")
    return redirect(url_for("users"))


def initialize_database():
    db.create_all()
    if not User.query.first():
        admin = User(username=os.getenv("ADMIN_USERNAME", "admin"), is_admin=True)
        admin.set_password(os.getenv("ADMIN_PASSWORD", "ChangeMe123!"))
        db.session.add(admin); db.session.commit()


with app.app_context():
    initialize_database()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
