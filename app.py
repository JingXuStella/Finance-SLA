import os
from datetime import date, datetime
from decimal import Decimal
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
url = os.getenv("DATABASE_URL", "sqlite:///finance.db").replace("postgres://", "postgresql://", 1)
app.config.update(SECRET_KEY=os.getenv("SECRET_KEY", "change-this-before-production"), SQLALCHEMY_DATABASE_URI=url, SQLALCHEMY_TRACK_MODIFICATIONS=False)
db = SQLAlchemy(app)
TYPES = {"主合同收入":"contract", "VO变更款项收入":"contract", "分包支出":"subcontract", "其他支出":"other"}
STATUSES = ["未开票", "部分开票", "已开票", "已收款"]

class User(db.Model):
 id=db.Column(db.Integer,primary_key=True); username=db.Column(db.String(64),unique=True,nullable=False); password_hash=db.Column(db.String(256),nullable=False); is_admin=db.Column(db.Boolean,default=False); created_at=db.Column(db.DateTime,default=datetime.utcnow)
 def set_password(self,p): self.password_hash=generate_password_hash(p)
 def check_password(self,p): return check_password_hash(self.password_hash,p)
class Project(db.Model):
 id=db.Column(db.Integer,primary_key=True); year=db.Column(db.Integer,index=True,nullable=False); name=db.Column(db.String(160),nullable=False); client=db.Column(db.String(160),default=""); manager=db.Column(db.String(80),default=""); contract_amount=db.Column(db.Numeric(14,2),default=0); subcontract_amount=db.Column(db.Numeric(14,2),default=0); other_cost=db.Column(db.Numeric(14,2),default=0); invoice_amount=db.Column(db.Numeric(14,2),default=0); invoice_status=db.Column(db.String(30),default="未开票"); notes=db.Column(db.Text,default=""); updated_at=db.Column(db.DateTime,default=datetime.utcnow,onupdate=datetime.utcnow); created_by=db.Column(db.String(64),default="")
 entries=db.relationship("LedgerEntry",backref="project",cascade="all, delete-orphan",lazy="select",order_by="LedgerEntry.payment_date.desc(), LedgerEntry.id.desc()")
 @property
 def totals(self):
  t={k:Decimal("0") for k in ["contract","subcontract","other","invoice"]}
  for e in self.entries: t[e.category]+=e.amount; t["invoice"]+=e.invoice_amount
  t["profit"]=t["contract"]-t["subcontract"]-t["other"]; return t
class LedgerEntry(db.Model):
 id=db.Column(db.Integer,primary_key=True); project_id=db.Column(db.Integer,db.ForeignKey("project.id"),index=True,nullable=False); payment_type=db.Column(db.String(40),nullable=False); category=db.Column(db.String(20),nullable=False); amount=db.Column(db.Numeric(14,2),default=0); invoice_amount=db.Column(db.Numeric(14,2),default=0); invoice_status=db.Column(db.String(30),default="未开票"); payment_date=db.Column(db.Date,default=date.today); notes=db.Column(db.Text,default="")

def me(): return db.session.get(User,session["user_id"]) if session.get("user_id") else None
def login_required(f):
 def w(*a,**k):
  if not me(): flash("请先登录。","warning"); return redirect(url_for("login"))
  return f(*a,**k)
 w.__name__=f.__name__; return w
def admin_required(f):
 def w(*a,**k):
  if not me() or not me().is_admin: flash("此操作仅限管理员。","danger"); return redirect(url_for("dashboard"))
  return f(*a,**k)
 w.__name__=f.__name__; return w
def amount(k):
 try:
  v=Decimal(request.form.get(k,"0") or "0")
  if v<0: raise ValueError
  return v
 except: raise ValueError("金额必须是大于或等于 0 的数字。")
def totals(ps):
 r={k:Decimal("0") for k in ["contract","subcontract","other","invoice","profit"]}
 for p in ps:
  for k,v in p.totals.items(): r[k]+=v
 return r
@app.context_processor
def ctx(): return {"current_user":me(),"now_year":datetime.now().year,"payment_types":TYPES,"invoice_statuses":STATUSES}
@app.template_filter("currency")
def currency(v): return f"¥{(v or 0):,.2f}"

@app.route("/login",methods=["GET","POST"])
def login():
 if me(): return redirect(url_for("dashboard"))
 if request.method=="POST":
  u=User.query.filter_by(username=request.form.get("username","").strip()).first()
  if u and u.check_password(request.form.get("password","")): session.clear();session["user_id"]=u.id;return redirect(url_for("dashboard"))
  flash("用户名或密码不正确。","danger")
 return render_template("login.html")
@app.route("/logout")
def logout(): session.clear();return redirect(url_for("login"))
@app.route("/")
@login_required
def dashboard():
 ys=[]
 for y, in db.session.query(Project.year).distinct().order_by(Project.year.desc()):
  ps=Project.query.filter_by(year=y).all(); ys.append({"year":y,"count":len(ps),"totals":totals(ps)})
 return render_template("dashboard.html",years=ys)
@app.route("/years/<int:year>")
@login_required
def year_detail(year):
 ps=Project.query.filter_by(year=year).order_by(Project.updated_at.desc()).all();return render_template("year_detail.html",year=year,projects=ps,totals=totals(ps))
@app.route("/projects/new",methods=["GET","POST"])
@login_required
def project_new():
 if request.method=="POST":
  try:
   p=Project(year=int(request.form["year"]),name=request.form["name"].strip(),client=request.form.get("client",""),manager=request.form.get("manager",""),notes=request.form.get("notes",""),created_by=me().username)
   if not p.name: raise ValueError("项目名称不能为空。")
   db.session.add(p);db.session.commit();return redirect(url_for("project_detail",project_id=p.id))
  except Exception as e: flash(str(e),"danger")
 return render_template("project_form.html",project=None)
@app.route("/projects/<int:project_id>")
@login_required
def project_detail(project_id): return render_template("project_detail.html",project=db.get_or_404(Project,project_id))
@app.route("/projects/<int:project_id>/edit",methods=["GET","POST"])
@login_required
def project_edit(project_id):
 p=db.get_or_404(Project,project_id)
 if request.method=="POST":
  try:
   p.year=int(request.form["year"]);p.name=request.form["name"].strip();p.client=request.form.get("client","");p.manager=request.form.get("manager","");p.notes=request.form.get("notes","")
   if not p.name: raise ValueError("项目名称不能为空。")
   db.session.commit();return redirect(url_for("project_detail",project_id=p.id))
  except Exception as e:flash(str(e),"danger")
 return render_template("project_form.html",project=p)
@app.route("/projects/<int:project_id>/entries/new",methods=["POST"])
@login_required
def entry_new(project_id):
 p=db.get_or_404(Project,project_id);return save_entry(None,p)
@app.route("/entries/<int:entry_id>/edit",methods=["POST"])
@login_required
def entry_edit(entry_id): return save_entry(db.get_or_404(LedgerEntry,entry_id),None)
def save_entry(e,p):
 try:
  typ=request.form["payment_type"]
  if typ not in TYPES:raise ValueError("款项类型无效。")
  if not e:e=LedgerEntry(project=p)
  e.payment_type=typ;e.category=TYPES[typ];e.amount=amount("amount");e.invoice_amount=amount("invoice_amount");e.invoice_status=request.form["invoice_status"];e.payment_date=datetime.strptime(request.form["payment_date"],"%Y-%m-%d").date();e.notes=request.form.get("notes","")
  if e.invoice_status not in STATUSES:raise ValueError("开票状态无效。")
  db.session.add(e);db.session.commit();flash("款项已保存。","success")
 except Exception as x:flash(str(x),"danger")
 return redirect(url_for("project_detail",project_id=(p or e.project).id))
@app.route("/entries/<int:entry_id>/delete",methods=["POST"])
@login_required
def entry_delete(entry_id):
 e=db.get_or_404(LedgerEntry,entry_id);p=e.project_id;db.session.delete(e);db.session.commit();return redirect(url_for("project_detail",project_id=p))

@app.route("/users",methods=["GET","POST"])
@admin_required
def users():
 if request.method=="POST":
  name,pw=request.form.get("username",""),request.form.get("password","")
  if len(name)<2 or len(pw)<8: flash("用户名至少 2 位，密码至少 8 位。","danger")
  elif User.query.filter_by(username=name).first(): flash("该用户名已经存在。","danger")
  else:
   u=User(username=name,is_admin=request.form.get("is_admin")=="on");u.set_password(pw);db.session.add(u);db.session.commit();return redirect(url_for("users"))
 return render_template("users.html",users=User.query.order_by(User.created_at.desc()).all())

def initialize():
 db.create_all()
 if not User.query.first():
  u=User(username=os.getenv("ADMIN_USERNAME","admin"),is_admin=True);u.set_password(os.getenv("ADMIN_PASSWORD","ChangeMe123!"));db.session.add(u);db.session.commit()
 for p in Project.query.all():
  if not p.entries and any([p.contract_amount,p.subcontract_amount,p.other_cost]):
   for typ,val,inv,status in [("主合同收入",p.contract_amount,p.invoice_amount,p.invoice_status),("分包支出",p.subcontract_amount,0,"未开票"),("其他支出",p.other_cost,0,"未开票")]:
    if val:db.session.add(LedgerEntry(project=p,payment_type=typ,category=TYPES[typ],amount=val,invoice_amount=inv,invoice_status=status,payment_date=date.today(),notes="由旧版汇总数据转换"))
   p.contract_amount=p.subcontract_amount=p.other_cost=p.invoice_amount=0
 db.session.commit()
with app.app_context():initialize()
if __name__=="__main__":app.run(host="0.0.0.0",port=int(os.getenv("PORT",5000)),debug=True)
