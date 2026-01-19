from django.core.management.base import BaseCommand
from exam.models import Paper, PaperQuestion


class Command(BaseCommand):
    help = '修复试卷题目的order字段，确保所有题目都有正确的序号'

    def handle(self, *args, **options):
        papers = Paper.objects.all()
        fixed_count = 0
        
        for paper in papers:
            paper_questions = paper.paper_questions.all().order_by('id')
            order = 1
            updated = False
            
            for pq in paper_questions:
                if pq.order != order:
                    pq.order = order
                    pq.save()
                    updated = True
                order += 1
            
            if updated:
                fixed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'已修复试卷 "{paper.name}" (ID: {paper.id}) 的题目序号')
                )
        
        if fixed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n成功修复 {fixed_count} 个试卷的题目序号')
            )
        else:
            self.stdout.write(self.style.SUCCESS('所有试卷的题目序号都是正确的，无需修复'))





