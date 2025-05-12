from __future__ import annotations

import flask_wtf
import wtforms
from flask_wtf.file import FileField


class NewProjectForm(flask_wtf.FlaskForm):  # type: ignore[misc]
    name = wtforms.fields.StringField("Project Name", validators=[wtforms.validators.DataRequired()])
    description = wtforms.fields.TextAreaField(
        "Description", render_kw={"placeholder": "Optional short project description"}
    )
    drone = wtforms.fields.SelectField("Drone", coerce=int)
    log_file = FileField("Drone log")
    submit = wtforms.fields.SubmitField("Add Project")


class EditProjectForm(flask_wtf.FlaskForm):  # type: ignore[misc]
    edit_project_before = wtforms.fields.HiddenField()
    edit_project_id = wtforms.fields.HiddenField()
    edit_name = wtforms.fields.StringField("Project Name", validators=[wtforms.validators.DataRequired()])
    edit_description = wtforms.fields.TextAreaField(
        "Description", render_kw={"placeholder": "Optional short project description"}
    )
    edit_drone = wtforms.fields.SelectField("Drone", coerce=int)
    edit_log_file = FileField("Drone log")
    edit_submit = wtforms.fields.SubmitField("Edit Project")


class NewDroneForm(flask_wtf.FlaskForm):  # type: ignore[misc]
    name = wtforms.fields.StringField("Drone Name", validators=[wtforms.validators.DataRequired()])
    camera_settings = wtforms.fields.TextAreaField(
        "Camera Settings",
        render_kw={
            "placeholder": "Optional description of camera settings used. \n"
            "Format, fps, etc. \n"
            "Useful if Drone is used with different settings",
            "rows": 4,
        },
    )
    submit = wtforms.fields.SubmitField("Add Drone")


class EditDroneForm(flask_wtf.FlaskForm):  # type: ignore[misc]
    edit_drone_before = wtforms.fields.HiddenField()
    edit_drone_id = wtforms.fields.HiddenField()
    edit_name = wtforms.fields.StringField("Drone Name", validators=[wtforms.validators.DataRequired()])
    edit_camera_settings = wtforms.fields.TextAreaField(
        "Camera Settings",
        render_kw={
            "placeholder": "Optional description of camera settings used. \n"
            "Format, fps, etc. \n"
            "Useful if Drone is used with different settings",
            "rows": 4,
        },
    )
    edit_submit = wtforms.fields.SubmitField("Edit Drone")
