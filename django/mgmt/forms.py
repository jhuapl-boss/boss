from django import forms
from bosscore.models import Channel
from bosscore.views.views_resource import DEFAULT_CUBOID_BUCKET_NAME

class UpdateForm(forms.Form):
    '''Custom base class for forms that need to support updating
    a subset of the field used to create the object'''

    '''The names of the fields that are used during an update'''
    UPDATE_FIELDS = []

    def is_update(self):
        '''Mark all fields not listed in UPDATE_FIELDS as readonly'''
        for field in self.fields:
            if not field in self.UPDATE_FIELDS:
                # DP NOTE: readonly doesn't work for ChoiceFields, as
                #          the user doesn't enter text, but selects a
                #          value. Using a CharField doesn't allow them
                #          to change the drop down, but still see the
                #          selected value
                if isinstance(self.fields[field], forms.ChoiceField):
                    self.fields[field] = forms.CharField()

                # DP NOTE: Using disabled means the values are not sent
                #          back to the server, which means if there is a
                #          validation error, the disabled fields will
                #          be empty and also cause validation errors
                #self.fields[field].disabled = True
                #self.fields[field].widget.attrs['disabled'] = True
                self.fields[field].widget.attrs['readonly'] = True
        return self

    @property
    def cleaned_update_data(self):
        '''Get cleaned_data with only the keys listed in UPDATE_FIELDS'''
        data = self.cleaned_data.copy()
        for key in list(data.keys()):
            if key not in self.UPDATE_FIELDS:
                del data[key]
        return data

# From: http://blog.corporatism.org/blog/2009/09/15/82/django_forcing_a_multiple_choice_widget_into_a_del
class ListTextInput(forms.TextInput):
    '''Widget that takes a list as input and produces a joined string TextInput'''
    def __init__(self, seperator=', ', **kwargs):
        self.seperator = seperator
        super(ListTextInput, self).__init__(**kwargs)

    def render(self, name, value, **kwargs):
        try:
            value = self.seperator.join(value)
        except TypeError:
            pass # Not an iterable
        return super(ListTextInput, self).render(name, value, **kwargs)

class DelimitedCharField(forms.CharField):
    '''Field that takes a list as input, produces a joined string TextInput and returns a list'''
    def __init__(self, seperator=', ', trim=True, **kwargs):
        self.widget = ListTextInput(seperator)
        self.delimiter = seperator
        self.trim = trim
        super(DelimitedCharField, self).__init__(**kwargs)

    def clean(self, value):
        val = super(DelimitedCharField, self).clean(value)
        vals = val.split(self.delimiter)
        if self.trim:
            vals = [v.strip() for v in vals]
        if len(vals) == 1 and vals[0] == '':
            vals = [] # handle the bahavior of split
        return vals

class UserForm(forms.Form):
    username = forms.CharField(help_text="Globally unique username")
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
    group_name = forms.CharField(label="Group Name", help_text="Globally unique name for the user group.")

class GroupMemberForm(forms.Form):
    user = forms.CharField()
    role = forms.ChoiceField(choices=[(c,c) for c in ['', 'member', 'maintainer', 'member+maintainer']])

class CollectionForm(UpdateForm):
    UPDATE_FIELDS = ['public']
    name = forms.CharField(label="Collection", help_text="Globally unique string identifier")
    public = forms.BooleanField(required=False, help_text="Give read access to all?")
    description = forms.CharField(required=False, help_text="Optional")

class CoordinateFrameForm(UpdateForm):
    UPDATE_FIELDS = ['name', 'description'] 

    name = forms.CharField(label="Coordinate Frame", help_text="Globally unique string identifier")
    description = forms.CharField(required=False, help_text="Optional")

    x_start = forms.IntegerField(help_text="Start point in X, inclusive. Typically 0")
    x_stop = forms.IntegerField(help_text="End point in X, exclusive")

    y_start = forms.IntegerField(help_text="Start point in Y, inclusive. Typically 0")
    y_stop = forms.IntegerField(help_text="End point in Y, exclusive")

    z_start = forms.IntegerField(help_text="Start point in Z, inclusive. Typically 0")
    z_stop = forms.IntegerField(help_text="End point in Z, exclusive")

    x_voxel_size = forms.IntegerField(help_text="Voxel dimension in X")
    y_voxel_size = forms.IntegerField(help_text="Voxel dimension in y")
    z_voxel_size = forms.IntegerField(help_text="Voxel dimension in z")
    voxel_unit = forms.ChoiceField(choices=[(c,c) for c in ['',
                                                            'nanometers',
                                                            'micrometers',
                                                            'millimeters',
                                                            'centimeters']],
                                   help_text="Unit of measure for voxel size")


class ExperimentForm(UpdateForm):
    UPDATE_FIELDS = ['name', 'public', 'description',
                     'num_hierarchy_levels',
                     'hierarch_method',
                     'num_time_samples',
                     'time_step',
                     'time_step_unit']

    name = forms.CharField(label="Experiment", help_text="A string identifier, unique to this Collection")
    public = forms.BooleanField(required=False, help_text="Give read access to all?")
    description = forms.CharField(required=False, help_text="Optional")

    coord_frame = forms.CharField(help_text="String identifier for this experiment's Coordinate Frame") # DP TODO: make a drop down with valid coord frame names
    num_hierarchy_levels = forms.IntegerField(help_text="Number of levels to render in the resolution hierarchy")
    hierarchy_method = forms.ChoiceField(choices=[(c,c) for c in ['', 'anisotropic', 'isotropic']],
                                         help_text="Downsampling method. See documentation for details.")
    num_time_samples = forms.IntegerField(help_text="Maximum number of time samples in the experiment (used for request validation). Non-time series data, set to 1")

    time_step = forms.IntegerField(required=False, help_text="(Optional) If time-series data, duration between samples.")
    time_step_unit = forms.ChoiceField(required=False,
                                       choices=[(c, c) for c in ['',
                                                                'nanoseconds',
                                                                'microseconds',
                                                                'milliseconds',
                                                                'seconds']],
                                       help_text="(Optional) Unit of measure for time step")

class MetaForm(UpdateForm):
    UPDATE_FIELDS = ['value']

    key = forms.CharField()
    value = forms.CharField(widget=forms.Textarea)

class ChannelForm(UpdateForm):
    # This list is for all users.  Users in the admin group get additional
    # fields when is_update() called.
    BASE_UPDATE_FIELDS = ['name', 'public', 'description',
                         'default_time_sample',
                         'base_resolution',
                         'sources', 'related']
    UPDATE_FIELDS = BASE_UPDATE_FIELDS.copy()

    # Currently, these fields are restricted to admins.
    ADMIN_ONLY_FIELDS = ['storage_type', 'bucket', 'cv_path']

    name = forms.CharField(label="Channel", help_text="String identifier unique to the experiment")
    public = forms.BooleanField(required=False, help_text="Give read access to all?")
    description = forms.CharField(required=False, help_text="Optional description")

    storage_type = forms.ChoiceField(choices=(('', ''),) + Channel.STORAGE_TYPE_CHOICES,
                                     required=False,
                                     help_text='Storage backend for this channel')

    bucket = forms.CharField(required=False,
                             empty_value=None,
                             help_text=f'(default is {DEFAULT_CUBOID_BUCKET_NAME})',
                             label='Bucket Name')
    
    cv_path = forms.CharField(required=False, 
                              empty_value=None,
                              help_text='Public S3 URI to Cloudvolume Dataset (start with / after the bucket name)',
                              label='CloudVolume Path')

    type = forms.ChoiceField(choices=[(c,c) for c in ['', 'image', 'annotation']],
                             help_text="image = source image dataset<br>annotation = label dataset")
    datatype = forms.ChoiceField(choices=[(c,c) for c in ['', 'uint8', 'uint16', 'uint64']],
                                 help_text="uint8 & uint16 for image channels<br>uint64 for annotation channels")

    base_resolution = forms.IntegerField(required=False,
                                         help_text="Resolution hierarchy level assumed to be 'native'. <br>Used primarily for dynamic resampling of annotation channels. Default to 0")
    default_time_sample = forms.IntegerField(required=False,
                                             help_text="Time sample used when omitted from a request. <br>For non-time series data always set to 0")
    sources = DelimitedCharField(label="Source Channel", required=False,
                                 help_text="Optional comma separated list of channels from which this channel is derived.<br>Useful for linking annotation to image channels")
    related = DelimitedCharField(label="Related Channels", required=False,
                                 help_text="Optional comma separated list of channels related to this channel.")

    def update_fields_if_admin(self):
        """
        Augment the set of fields that are updatable if user had admin privileges.
        """
        self.UPDATE_FIELDS = self.BASE_UPDATE_FIELDS.copy()
        is_admin = self.data.get('is_admin', False)
        if is_admin:
            self.UPDATE_FIELDS.extend(self.ADMIN_ONLY_FIELDS)

    def is_update(self):
        """
        Override base class' is_update() so admins can update additional fields.
        """
        self.update_fields_if_admin()
        return super().is_update()

    @property
    def cleaned_update_data(self):
        """
        Override base class' property so admins can update additional fields.
        """
        self.update_fields_if_admin()
        return super().cleaned_update_data

    def disable_non_admin_fields(self):
        """
        Disable fields that only admins can access.  Use this when providing a
        create form for the non-admin user.
        """
        for name in self.ADMIN_ONLY_FIELDS:
            self.fields[name].disabled = True


def PermField():
    #perms = ['read', 'add', 'update', 'delete', 'assign_group', 'remove_group']
    #return forms.MultipleChoiceField(choices=[(c,c) for c in perms])
    perms = ['read', 'read+addmeta', 'read+fullmeta', 'write', 'admin', 'admin+delete']
    return forms.ChoiceField(choices=[(c,c) for c in perms])

class ResourcePermissionsForm(forms.Form):
    group = forms.CharField()
    permissions = PermField()

class GroupPermissionsForm(forms.Form):
    collection = forms.CharField()
    experiment = forms.CharField(required=False)
    channel = forms.CharField(required=False)
    permissions = PermField()

    def clean(self):
        super(GroupPermissionsForm, self).clean()

        channel = self.cleaned_data.get('channel')
        experiment = self.cleaned_data.get('experiment')
        collection = self.cleaned_data.get('collection')

        if channel and not experiment:
            raise forms.ValidationError("Experiment required")

        if experiment and not collection:
            raise forms.ValidationError("Collection required")

