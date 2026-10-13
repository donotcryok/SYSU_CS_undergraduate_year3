from django.db import models

class Book(models.Model):
    # 对应图2：book_id (PK, char(8), not null)
    book_id = models.CharField(max_length=8, primary_key=True, verbose_name="图书编号")
    
    # 对应图2：book_name (nvarchar(50), not null)
    book_name = models.CharField(max_length=50, verbose_name="图书名称")
    
    # 对应图2：book_isbn (char(17), not null)
    book_isbn = models.CharField(max_length=17, verbose_name="ISBN")
    
    # 对应图2：book_author (nvarchar(10), not null)
    book_author = models.CharField(max_length=10, verbose_name="作者")
    
    # 对应图2：book_publisher (nvarchar(50), not null)
    book_publisher = models.CharField(max_length=50, verbose_name="出版社")
    
    # 对应图2：book_price (money, not null) -> Django用DecimalField对应money
    book_price = models.DecimalField(max_digits=19, decimal_places=4, verbose_name="价格")
    
    # 对应图2：interviews_times (int, not null)
    interviews_times = models.IntegerField(verbose_name="借阅次数", default=0)

    class Meta:
        managed = False  # 关键：使用现有的表
        db_table = 'book'
        verbose_name = '图书'
        verbose_name_plural = '图书管理'

    def __str__(self):
        return self.book_name