import flask_wtf
import wtforms
from flask_wtf.file import FileField, FileRequired


class NewProjectForm(flask_wtf.FlaskForm):
    name = wtforms.fields.StringField(u'Project Name', validators=[wtforms.validators.DataRequired()])
    description = wtforms.fields.TextAreaField(u'Description', render_kw={'placeholder': 'Optional short project description'})
    drone = wtforms.fields.SelectField(u'Drone')
    log_file = FileField(u'Drone log', validators=[FileRequired()])
    submit = wtforms.fields.SubmitField(u'Add Project')


class EditProjectForm(flask_wtf.FlaskForm):
    edit_project_before = wtforms.fields.HiddenField()
    edit_name = wtforms.fields.StringField(u'Project Name', validators=[wtforms.validators.DataRequired()])
    edit_description = wtforms.fields.TextAreaField(u'Description', render_kw={'placeholder': 'Optional short project description'})
    edit_drone = wtforms.fields.SelectField(u'Drone')
    edit_log_file = FileField(u'Drone log')
    edit_submit = wtforms.fields.SubmitField(u'Edit Project')


class NewDroneForm(flask_wtf.FlaskForm):
    name = wtforms.fields.StringField(u'Drone Name', validators=[wtforms.validators.DataRequired()])
    camera_settings = wtforms.fields.TextAreaField(u'Camera Settings', render_kw={'placeholder': 'Optional description of camera settings used. \n'
                                                                                  'Format, fps, etc. \n'
                                                                                  'Useful if Drone is used with different settings',
                                                                                  'rows': 4})
    submit = wtforms.fields.SubmitField(u'Add Drone')


class EditDroneForm(flask_wtf.FlaskForm):
    edit_drone_before = wtforms.fields.HiddenField()
    edit_name = wtforms.fields.StringField(u'Drone Name', validators=[wtforms.validators.DataRequired()])
    edit_camera_settings = wtforms.fields.TextAreaField(u'Camera Settings', render_kw={'placeholder': 'Optional description of camera settings used. \n'
                                                                                       'Format, fps, etc. \n'
                                                                                       'Useful if Drone is used with different settings',
                                                                                       'rows': 4})
    edit_submit = wtforms.fields.SubmitField(u'Edit Drone')
