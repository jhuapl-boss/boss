from django import forms

class UserForm(forms.Form):
    username = forms.CharField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())
    verify_password = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        super(UserForm, self).clean()
        password = self.cleaned_data.get('password')
        verify_password = self.cleaned_data.get('verify_password')

        if password or verify_password:
            if password != verify_password:
                raise forms.ValidationError("Passwords don't match")

class RoleForm(forms.Form):
    role = forms.ChoiceField(choices=[(c,c) for c in ['', 'user-manager', 'resource-manager']])

class GroupForm(forms.Form):
    group_name = forms.CharField()

class GroupMemberForm(forms.Form):
    user = forms.CharField()
    role = forms.ChoiceField(choices=[(c,c) for c in ['', 'member', 'maintainer', 'member+maintainer']])

class CollectionForm(forms.Form):
    collection = forms.CharField()
    description = forms.CharField(required=False)

class CoordinateFrameForm(forms.Form):
    name = forms.CharField(label="Coordinate Frame")
    description = forms.CharField(required=False)

    x_start = forms.IntegerField()
    x_stop = forms.IntegerField()

    y_start = forms.IntegerField()
    y_stop = forms.IntegerField()

    z_start = forms.IntegerField()
    z_stop = forms.IntegerField()

    x_voxel_size = forms.IntegerField()
    y_voxel_size = forms.IntegerField()
    z_voxel_size = forms.IntegerField()
    voxel_unit = forms.ChoiceField(choices=[(c,c) for c in ['',
                                                            'nanometers',
                                                            'micrometers',
                                                            'millimeters',
                                                            'centimeters']])

    time_step = forms.IntegerField(required=False)
    time_step_unit = forms.ChoiceField(required=False,
                                       choices=[(c,c) for c in ['',
                                                                'nanoseconds',
                                                                'microseconds',
                                                                'milliseconds',
                                                                'seconds']])

class ExperimentForm(forms.Form):
    name = forms.CharField(label="Experiment")
    description = forms.CharField(required=False)

    coord_frame = forms.CharField() # DP TODO: make a drop down with valid coord frame names
    num_hierarchy_levels = forms.IntegerField()
    hierarchy_method = forms.ChoiceField(choices=[(c,c) for c in ['', 'near_iso', 'iso', 'slice']])
    num_time_samples = forms.IntegerField()

class MetaForm(forms.Form):
    key = forms.CharField()
    value = forms.CharField(widget=forms.Textarea)

class ChannelForm(forms.Form):
    name = forms.CharField(label="Channel")
    description = forms.CharField(required=False)

    type = forms.ChoiceField(choices=[(c,c) for c in ['', 'image', 'annotation']])
    datatype = forms.ChoiceField(choices=[(c,c) for c in ['', 'uint8', 'uint16', 'uint32', 'uint64']])

    base_resolution = forms.IntegerField(required=False)
    default_time_sample = forms.IntegerField(required=False)
    source = forms.CharField(required=False) # DP TODO: create custom field type that splits on '.'
    related = forms.CharField(required=False)

