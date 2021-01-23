from django.contrib import admin
from django.http.response import HttpResponse
from .models import Candidate
from django.db.models import Q
# from interview.candidate_fieldset import default_fieldsets, default_fieldsets_first, default_fieldsets_second
from interview import candidate_fieldset as cf
from interview import dingtalk

import logging
import csv
from datetime import datetime

logger = logging.getLogger(__name__)

# 定义导出的字段
exportabel_fields = ('username', 'city', 'phone', 'bachelor_school', 'master_school', 'degree', 'first_result',
                     'first_interviewer_user', 'second_result', 'second_interviewer_user', 'hr_result',
                     'hr_interviewer_user', 'first_score', 'second_score', 'hr_score')

# define notify action
def notify_interviewer(modeladmin, request, queryset):
    candidates = ""
    interviewers = ""
    for obj in queryset:
        candidates = obj.username + "," + candidates
        interviewers = obj.first_interviewer_user.username + "," + interviewers
        # 还需要处理interviewers去重
    dingtalk.send(f"\n候选人: {candidates} 进入面试环节\n。亲爱的面试官，请做好准备面试：{interviewers}")

notify_interviewer.short_description = '通知一面面试官'

# define export action
def export_model_as_csv(modeladmin, request, queryset):
    """
    通过定义action,在action方法里实现导出逻辑，把函数方法注册到admin的action里面，界面上就会多出导出菜单
    """
    response = HttpResponse(content_type='text/csv')
    field_list = exportabel_fields
    response['Content-Disposition'] = 'attachment; filename=%s-%s.csv' % (
        'recruitment-candidate-list',
        datetime.now().strftime('%Y-%m-%d-%H-%M-%S'),
    )

    # 写入表头
    writer = csv.writer(response)
    writer.writerow(
        # 查询到verboes_name填入csv表头
        [queryset.model._meta.get_field(f).verbose_name.title() for f in field_list]
    )
    for obj in queryset:
        # 单行记录，写到csv
        csv_line_values = []
        for field in field_list:
            field_obj = queryset.model._meta.get_field(field)
            field_value = field_obj.value_from_object(obj)
            csv_line_values.append(field_value)
        writer.writerow(csv_line_values)

    logger.info(f"{request.user} exported {len(queryset)} candidate records")
    return response


# 定义函数属性
export_model_as_csv.short_description = '导出为CSV文件'
export_model_as_csv.allowed_permissions = ('export',)


# 候选人管理
class CandidateAdmin(admin.ModelAdmin):
    #
    actions = [export_model_as_csv, notify_interviewer]

    # 检测用户是否有导出权限
    def has_export_permission(self, request):
        opts = self.opts
        # return request.user.has_perm('%s.%s' % (opts.app_label, "export"))
        return request.user.has_perm(f'{opts.app_label}.{"export"}')


    # 设置不显示的字段
    exclude = ('creator', 'created_time', 'updated_time')
    # 设置显示的字段
    list_display = ('username', 'city', 'bachelor_school', 'first_score', 'first_result', 'first_interviewer_user',
                    'second_score', 'second_result', 'second_interviewer_user',
                    'hr_score', 'hr_result', 'hr_interviewer_user', 'last_editor')
    # 筛选
    list_filter = ('city', 'first_result', 'second_result', 'hr_result',
                   'first_interviewer_user', 'second_interviewer_user', 'hr_interviewer_user')
    # 排序
    ordering = ('hr_result', 'second_result', 'first_result')

    # 搜索,查询字段
    search_fields = ('username', 'phone', 'email', 'bachelor_school')

    #获取组名
    def get_group_names(self, user):
        group_names = []
        for g in user.groups.all():
            group_names.append(g.name)
        return group_names

    # 对于非管理员，非HR，获取一面面试官或者二面面试官的候选人集合
    def get_queryset(self, request):   # show data only owner by user
        qs = super(CandidateAdmin, self).get_queryset(request)
        group_names = self.get_group_names(request.user)
        if request.user.is_superuser or 'hr' in group_names:
            return qs
        return Candidate.objects.filter(
            # 一面面试官等于当前用户或二面面试官等于当前用户
            Q(first_interviewer_user=request.user) | Q(second_interviewer_user=request.user)
        )

    # 设置字段只读
    # readonly_fields = ('first_interviewer_user','second_interviewer_user')
    # get_readonly_fields 这个方法能获取到readonly_fields
    def get_readonly_fields(self, request, obj):
        # 取出用户所在组名
        group_names = self.get_group_names(request.user)
        # 如果interview在这个群组里面，
        if 'interviewer' in group_names:
            logger.info(f"interviewer is user's for {request.user.username}")
            # 返回readonly_field所取的字段
            return ('first_interviewer_user', 'second_interviewer_user',)
        # hr不返回
        return ()

    # 设置字段批量编辑
    # list_editable = ('first_interviewer_user','second_interviewer_user')
    def get_list_editable(self,request):
        group_names = self.get_group_names(request.user)
        # 如果是超级管理员或者hr在这个群组里面
        if request.user.is_superuser or 'hr' in group_names:
            return ('first_interviewer_user', 'second_interviewer_user',)
        return ()
    #覆盖modelAdmin父类的get_changelist
    def get_changelist_instance(self, request):
        self.list_editable = self.get_list_editable(request)
        return super(CandidateAdmin, self).get_changelist_instance(request)



    # 一面面试官仅填写一面反馈，二面面试官仅填写二面反馈
    def get_fieldsets(self, request, obj=None):
        group_names = self.get_group_names(request.user)
        # 如果登录用户为一面面试官，并在组里面
        if 'interviewer' in group_names and obj.first_interviewer_user == request.user:
            return cf.default_fieldsets_first
        # 如果登录用户为二面面试官，并在组里面
        if 'interviewer' in group_names and obj.second_interviewer_user == request.user:
            return cf.default_fieldsets_second
        return cf.default_fieldsets

admin.site.register(Candidate, CandidateAdmin)
