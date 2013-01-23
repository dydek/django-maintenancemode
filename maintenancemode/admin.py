import datetime
from django.contrib import admin
from django import forms
from maintenancemode.models import Maintenance, IgnoredURL, MaintenanceLog

class MaintenanceAdminForm(forms.ModelForm):
    summary = forms.CharField(widget=forms.Textarea(), required=False)
    reason = forms.CharField(widget=forms.Textarea(), required=False)

    class Meta:
        model = Maintenance

    def __init__(self, *args, **kwargs):
        super(MaintenanceAdminForm, self).__init__(*args, **kwargs)
        if 'instance' in kwargs:
            self.instance = kwargs['instance']
            if self.instance.is_being_performed:
                #add summary field
                self.fields['summary'].required = True
            else:
                #add reason field
                self.fields['reason'].required = True

    def clean(self):
        cd = self.cleaned_data
        print cd
        if 'summary' in cd and cd['summary'] and cd['is_being_performed']:
            cd['is_being_performed'] = False
        if 'reason' in cd and cd['reason'] and not cd['is_being_performed']:
            cd['is_being_performed'] = True
        return cd


class IgnoredURLInline(admin.TabularInline):
    model = IgnoredURL
    extra = 3

class MaintenanceAdmin(admin.ModelAdmin):
    inlines = [IgnoredURLInline, ]
    list_display = ['__unicode__', 'is_being_performed']
    readonly_fields = ('site',)
    actions = None
    form = MaintenanceAdminForm

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(MaintenanceAdmin, self).get_fieldsets(request, obj)
        if obj:
            obj = Maintenance.objects.get(pk=obj.pk)
            if obj.is_being_performed:
                fieldsets[0][1]['fields'] = ['is_being_performed','summary','site']
            else:
                fieldsets[0][1]['fields'] = ['is_being_performed','reason', 'site']
        return fieldsets

    def save_model(self, request, obj, form, change):
        print obj.is_being_performed
        if obj.is_being_performed:
            log = MaintenanceLog()
            log.date_start = datetime.datetime.now()
            log.reason = form.cleaned_data['reason']
            log.user = request.user
        else:
            log = MaintenanceLog.objects.filter(date_stop=None)[0]
            log.date_stop = datetime.datetime.now()
            log.summary = form.cleaned_data['summary']
        log.save()
        return super(MaintenanceAdmin, self).save_model(request, obj, form, change)

admin.site.register(Maintenance, MaintenanceAdmin)
