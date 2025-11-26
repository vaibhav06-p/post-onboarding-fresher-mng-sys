from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = 'change_this_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'SQLALCHEMY_DATABSE_URI',
    'mysql+pymysql://root:rootpassword@db:3306/fresher_mng'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Trainer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    batches = db.relationship('Batch', backref='trainer', lazy=True)


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    domain = db.Column(db.String(120), nullable=True)
    doj = db.Column(db.Date, nullable=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), nullable=True)

    evaluations = db.relationship('Evaluation', backref='employee', lazy=True)
    allocations = db.relationship('ProjectAllocation', backref='employee', lazy=True)
    feedbacks = db.relationship('Feedback', backref='employee', lazy=True)


class Batch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    domain = db.Column(db.String(120), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainer.id'), nullable=False)

    employees = db.relationship('Employee', backref='batch', lazy=True)
    evaluations = db.relationship('Evaluation', backref='batch', lazy=True)


class Evaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), nullable=False)
    m1_marks = db.Column(db.Integer, nullable=True)
    sprint_marks = db.Column(db.Integer, nullable=True)
    l1_marks = db.Column(db.Integer, nullable=True)
    aggregate = db.Column(db.Float, nullable=True)
    result = db.Column(db.String(10), nullable=True)


class ProjectAllocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    interview_date = db.Column(db.Date, nullable=True)
    project_name = db.Column(db.String(120), nullable=True)
    project_domain = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(20), nullable=True)


class Feedback(db.Model):
    __tablename__ = "feedback"
    id = db.Column(db.Integer, primary_key=True)

    trainer_id = db.Column(db.Integer, db.ForeignKey("trainer.id"), nullable=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)

    # numeric trainer ratings (1-5)
    trainer_q1 = db.Column(db.Integer, nullable=True)
    trainer_q2 = db.Column(db.String(8), nullable=True)   # yes/no or numeric stored as string
    trainer_q3 = db.Column(db.Integer, nullable=True)
    trainer_q4 = db.Column(db.String(8), nullable=True)   # yes/no
    trainer_q5_text = db.Column(db.Text, nullable=True)   # descriptive suggestions

    # curriculum fields
    curriculum_q1 = db.Column(db.String(8), nullable=True)  # yes/no
    curriculum_q2 = db.Column(db.Integer, nullable=True)
    curriculum_q3_text = db.Column(db.Text, nullable=True)
    curriculum_q4_text = db.Column(db.Text, nullable=True)
    curriculum_q5 = db.Column(db.Integer, nullable=True)

    # general comments + overall star rating
    comments = db.Column(db.Text, nullable=True)
    overall_rating = db.Column(db.Integer, nullable=True)


with app.app_context():
    db.create_all()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/trainer/register', methods=['GET', 'POST'])
def register_trainer():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        existing = Trainer.query.filter_by(email=email).first()
        if existing:
            flash('Trainer with this email already exists.')
            return redirect(url_for('register_trainer'))

        trainer = Trainer(name=name, email=email, password=password)
        db.session.add(trainer)
        db.session.commit()
        flash('Trainer registered successfully. Please log in.')
        return redirect(url_for('login_trainer'))
    return render_template('register_trainer.html')


@app.route('/trainer/login', methods=['GET', 'POST'])
def login_trainer():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        trainer = Trainer.query.filter_by(email=email, password=password).first()
        if trainer:
            session['trainer_id'] = trainer.id
            session['role'] = 'trainer'
            return redirect(url_for('trainer_dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login_trainer.html')


@app.route('/trainer/logout')
def trainer_logout():
    session.clear()
    return redirect(url_for('home'))


# --- register_employee (remove domain from registration) ---
@app.route("/employee/register", methods=["GET", "POST"])
def register_employee():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        doj_str = request.form.get("doj")

        doj = None
        if doj_str:
            try:
                doj = datetime.strptime(doj_str, "%Y-%m-%d").date()
            except ValueError:
                doj = None

        if Employee.query.filter_by(email=email).first():
            flash("An employee with that email already exists.", "warning")
            return redirect(url_for("register_employee"))

        employee = Employee(
            name=name,
            email=email,
            password=password,    # plain-text password
            domain=None,          # domain will be assigned by trainer
            doj=doj,
        )
        db.session.add(employee)
        db.session.commit()
        flash("Employee registered successfully. Please log in.", "success")
        return redirect(url_for("login_employee"))

    return render_template("register_employee.html")


# @app.route("/employee/register", methods=["GET", "POST"])
# def register_employee():
#     if request.method == "POST":
#         name = request.form["name"].strip()
#         email = request.form["email"].strip().lower()
#         password = request.form["password"]
#         doj_str = request.form.get("doj")

#         doj = None
#         if doj_str:
#             try:
#                 doj = datetime.strptime(doj_str, "%Y-%m-%d").date()
#             except ValueError:
#                 doj = None

#         if Employee.query.filter_by(email=email).first():
#             flash("An employee with that email already exists.", "warning")
#             return redirect(url_for("register_employee"))

#         employee = Employee(
#             name=name,
#             email=email,
#             password=password,    # store plain password
#             domain=None,          # domain assigned later by trainer
#             doj=doj,
#         )
#         db.session.add(employee)
#         db.session.commit()
#         flash("Employee registered successfully. Please log in.", "success")
#         return redirect(url_for("login_employee"))

#     return render_template("register_employee.html")


@app.route("/employee/login", methods=["GET", "POST"])
def login_employee():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        employee = Employee.query.filter_by(email=email).first()
        if employee and employee.password == password:
            session.clear()
            session["employee_id"] = employee.id
            session["role"] = "employee"
            flash("Logged in as employee.", "success")
            return redirect(url_for("employee_dashboard"))
        else:
            flash("Invalid credentials.", "danger")

    return render_template("login_employee.html")



@app.route('/employee/logout')
def employee_logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/trainer/dashboard')
def trainer_dashboard():
    if session.get('role') != 'trainer':
        return redirect(url_for('home'))

    trainer_id = session.get('trainer_id')
    trainer = Trainer.query.get(trainer_id)
    batches = Batch.query.filter_by(trainer_id=trainer_id).all()
    return render_template('trainer_dashboard.html', trainer=trainer, batches=batches)


@app.route('/trainer/add_batch', methods=['POST'])
def add_batch():
    if session.get('role') != 'trainer':
        return redirect(url_for('home'))

    name = request.form['name']
    domain = request.form['domain']
    start_date_str = request.form['start_date']

    start_date = None
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

    batch = Batch(
        name=name,
        domain=domain,
        start_date=start_date,
        trainer_id=session['trainer_id']
    )
    db.session.add(batch)
    db.session.commit()
    return redirect(url_for('trainer_dashboard'))


# --- batch_detail (include all_employees for dropdown & link to view performance) ---
@app.route("/trainer/batch/<int:batch_id>")
def batch_detail(batch_id):
    if session.get("role") != "trainer":
        flash("Please login as trainer to access that page.", "warning")
        return redirect(url_for("home"))

    batch = Batch.query.get_or_404(batch_id)
    employees = Employee.query.filter_by(batch_id=batch_id).order_by(Employee.id).all()
    all_employees = Employee.query.order_by(Employee.id).all()
    evaluations = Evaluation.query.filter_by(batch_id=batch_id).all()
    return render_template(
        "batch_detail.html",
        batch=batch,
        employees=employees,
        evaluations=evaluations,
        all_employees=all_employees
    )



# --- assign_employee_to_batch (trainer assigns domain when assigning) ---
@app.route("/trainer/assign_employee_to_batch", methods=["POST"])
def assign_employee_to_batch():
    if session.get("role") != "trainer":
        return redirect(url_for("home"))

    try:
        employee_id = int(request.form["employee_id"])
        batch_id = int(request.form["batch_id"])
    except (KeyError, ValueError):
        flash("Invalid input.", "danger")
        return redirect(url_for("trainer_dashboard"))

    domain_for_employee = request.form.get("domain") or None
    employee = Employee.query.get_or_404(employee_id)
    employee.batch_id = batch_id
    # Trainer assigns the domain while adding to batch
    if domain_for_employee:
        employee.domain = domain_for_employee.strip()
    db.session.commit()
    flash("Employee assigned to batch and domain set.", "success")
    return redirect(url_for("batch_detail", batch_id=batch_id))


@app.route('/trainer/edit_employee/<int:employee_id>', methods=['GET', 'POST'])
def edit_employee(employee_id):
    if session.get('role') != 'trainer':
        return redirect(url_for('home'))

    employee = Employee.query.get_or_404(employee_id)

    if request.method == 'POST':
        employee.name = request.form['name']
        employee.domain = request.form['domain']
        doj_str = request.form.get('doj')
        if doj_str:
            employee.doj = datetime.strptime(doj_str, '%Y-%m-%d').date()
        db.session.commit()
        flash('Employee information updated.')
        if employee.batch_id:
            return redirect(url_for('batch_detail', batch_id=employee.batch_id))
        return redirect(url_for('trainer_dashboard'))

    return render_template('edit_employee.html', employee=employee)


@app.route('/trainer/edit_evaluation/<int:employee_id>', methods=['POST'])
def edit_evaluation(employee_id):
    if session.get('role') != 'trainer':
        return redirect(url_for('home'))

    employee = Employee.query.get_or_404(employee_id)
    batch_id = int(request.form['batch_id'])

    evaluation = Evaluation.query.filter_by(employee_id=employee_id, batch_id=batch_id).first()
    if not evaluation:
        evaluation = Evaluation(employee_id=employee_id, batch_id=batch_id)

    evaluation.m1_marks = int(request.form.get('m1_marks') or 0)
    evaluation.sprint_marks = int(request.form.get('sprint_marks') or 0)
    evaluation.l1_marks = int(request.form.get('l1_marks') or 0)

    evaluation.aggregate = (evaluation.m1_marks + evaluation.sprint_marks + evaluation.l1_marks) / 3.0
    evaluation.result = 'Pass' if evaluation.aggregate >= 60 else 'Fail'

    db.session.add(evaluation)
    db.session.commit()
    flash('Evaluation updated.')

    return redirect(url_for('batch_detail', batch_id=batch_id))


# inside app.py - replace allocate_project route
@app.route("/trainer/allocate_project/<int:employee_id>", methods=["POST"])
def allocate_project(employee_id):
    if session.get("role") != "trainer":
        return redirect(url_for("home"))

    employee = Employee.query.get_or_404(employee_id)

    latest_eval = (
        Evaluation.query.filter_by(employee_id=employee_id)
        .order_by(Evaluation.id.desc())
        .first()
    )
    if not latest_eval or latest_eval.result != "Pass":
        flash("Employee must have passed evaluations before project allocation.", "warning")
        if employee.batch_id:
            return redirect(url_for("batch_detail", batch_id=employee.batch_id))
        return redirect(url_for("trainer_dashboard"))

    interview_date_str = request.form.get("interview_date")
    # trainer no longer provides project_name; only the domain
    project_domain = request.form.get("project_domain")

    interview_date = None
    if interview_date_str:
        try:
            interview_date = datetime.strptime(interview_date_str, "%Y-%m-%d").date()
        except ValueError:
            interview_date = None

    allocation = ProjectAllocation(
        employee_id=employee_id,
        interview_date=interview_date,
        project_name=None,
        project_domain=project_domain,
        status="Scheduled",
    )
    db.session.add(allocation)
    db.session.commit()
    flash("Project allocation and interview scheduled.", "success")

    if employee.batch_id:
        return redirect(url_for("batch_detail", batch_id=employee.batch_id))
    return redirect(url_for("trainer_dashboard"))



@app.route('/employee/dashboard')
def employee_dashboard():
    if session.get('role') != 'employee':
        return redirect(url_for('home'))

    employee_id = session.get('employee_id')
    employee = Employee.query.get_or_404(employee_id)
    evaluations = Evaluation.query.filter_by(employee_id=employee_id).all()
    allocations = ProjectAllocation.query.filter_by(employee_id=employee_id).all()

    return render_template('employee_dashboard.html', employee=employee, evaluations=evaluations, allocations=allocations)


@app.route('/employee/feedback', methods=['GET', 'POST'])
def feedback():
    if session.get('role') != 'employee':
        return redirect(url_for('home'))

    employee_id = session.get('employee_id')
    employee = Employee.query.get_or_404(employee_id)
    trainer_id = employee.batch.trainer_id if employee.batch else None

    if request.method == 'POST':
        fb = Feedback(
            trainer_id=trainer_id,
            employee_id=employee_id,
            trainer_q1=int(request.form['trainer_q1']),
            trainer_q2=int(request.form['trainer_q2']),
            trainer_q3=int(request.form['trainer_q3']),
            trainer_q4=int(request.form['trainer_q4']),
            trainer_q5=int(request.form['trainer_q5']),
            curriculum_q1=int(request.form['curriculum_q1']),
            curriculum_q2=int(request.form['curriculum_q2']),
            curriculum_q3=int(request.form['curriculum_q3']),
            curriculum_q4=int(request.form['curriculum_q4']),
            curriculum_q5=int(request.form['curriculum_q5']),
            comments=request.form.get('comments')
        )
        db.session.add(fb)
        db.session.commit()
        return redirect(url_for('thank_you'))

    return render_template('feedback.html', employee=employee)
# --- New: view_performance (trainer) ---
@app.route("/trainer/batch/<int:batch_id>/performance")
def view_performance(batch_id):
    if session.get("role") != "trainer":
        flash("Please login as trainer to access that page.", "warning")
        return redirect(url_for("home"))

    batch = Batch.query.get_or_404(batch_id)
    employees = Employee.query.filter_by(batch_id=batch_id).order_by(Employee.id).all()

    # build performance rows
    rows = []
    for emp in employees:
        # get latest evaluation for this employee in this batch
        eval = (
            Evaluation.query.filter_by(employee_id=emp.id, batch_id=batch_id)
            .order_by(Evaluation.id.desc())
            .first()
        )

        # defaults
        m1 = sprint = l1 = None
        m1_status = sprint_status = l1_status = "-"
        aggregate = "-"
        final_result = "-"

        if eval:
            m1 = eval.m1_marks
            sprint = eval.sprint_marks
            l1 = eval.l1_marks

            # per-assessment status: Pass if score >=60, Fail if <60, '-' if None
            if m1 is not None:
                m1_status = "Pass" if m1 >= 60 else "Fail"
            if sprint is not None:
                sprint_status = "Pass" if sprint >= 60 else "Fail"
            if l1 is not None:
                l1_status = "Pass" if l1 >= 60 else "Fail"

            # aggregate only if all three present
            if (m1 is not None) and (sprint is not None) and (l1 is not None):
                agg_val = (m1 + sprint + l1) / 3.0
                aggregate = round(agg_val, 2)
                # final pass only if aggregate >=60 AND each assessment individually passed
                if aggregate >= 60 and m1_status == "Pass" and sprint_status == "Pass" and l1_status == "Pass":
                    final_result = "Pass"
                else:
                    final_result = "Fail"
            else:
                # one or more missing => final_result remains '-'
                final_result = "-"

        rows.append({
            "employee": emp,
            "m1": m1,
            "m1_status": m1_status,
            "sprint": sprint,
            "sprint_status": sprint_status,
            "l1": l1,
            "l1_status": l1_status,
            "aggregate": aggregate,
            "final_result": final_result
        })

    return render_template("performance.html", batch=batch, rows=rows)


@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')


if __name__ == '__main__':
    app.run(debug=True)
