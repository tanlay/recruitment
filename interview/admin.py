from django.contrib import admin
from django.http.response import HttpResponse
from .models import Candidate

import logging
import csv
from datetime import datetime

logger = logging.getLogger(__name__)

# 定义导出的字段
exportabel_fields = ('username', 'city', 'phone', 'bachelor_school', 'master_school', 'degree', 'first_result',
                     'first_interviewer_user', 'second_result', 'second_interviewer_user', 'hr_result',
                     'hr_interviewer_user', 'first_score', 'second_score', 'hr_score')


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


# 候选人管理
class CandidateAdmin(admin.ModelAdmin):
    #
    actions = [export_model_as_csv, ]

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
    # 设置字段分组
    fieldsets = (
        ('用户基础信息', {'fields': (("userid", "username", "city", "phone"), ("email", "apply_position", "born_address"),
                               ("gender", "candidate_remark"), ("bachelor_school", "master_school", "doctor_school"),
                               ("major", "degree"), ("test_score_of_general_ability", "paper_score"), "last_editor")}),
        ('第一轮面试记录', {'fields': (
        ("first_score", "first_learning_ability", "first_professional_competency"), "first_advantage",
        "first_disadvantage", "first_result", "first_recommend_position", "first_interviewer_user", "first_remark")}),
        ('复试面试记录', {'fields': (("second_score", "second_learning_ability", "second_professional_competency"),
                               ("second_pursue_of_excellence", "second_communication_ability", "second_pressure_score"),
                               "second_advantage", "second_disadvantage", "second_result", "second_recommend_position",
                               "second_interviewer_user", "second_remark")}),
        ('HR面试记录', {'fields': (("hr_score", "hr_responsibility", "hr_communication_ability"),
                               ("hr_logic_ability", "hr_potential", "hr_stability"), "hr_advantage", "hr_disadvantage",
                               "hr_result", "hr_interviewer_user", "hr_remark")}),
    )


admin.site.register(Candidate, CandidateAdmin)
