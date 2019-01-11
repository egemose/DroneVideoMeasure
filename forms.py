from flask_wtf import FlaskForm
from wtforms.fields import SubmitField, StringField, TextAreaField, HiddenField
from wtforms.validators import DataRequired


class NewProjectForm(FlaskForm):
    name = StringField(u'Project Name', validators=[DataRequired()])
    description = TextAreaField(u'Description', render_kw={'placeholder': 'Optional short project description'})
    submit = SubmitField(u'Add Project')


class EditProjectForm(FlaskForm):
    edit_project_before = HiddenField()
    edit_name = StringField(u'Project Name', validators=[DataRequired()])
    edit_description = TextAreaField(u'Description', render_kw={'placeholder': 'Optional short project description'})
    edit_submit = SubmitField(u'Edit Project')
