from django import forms
from .models import Book

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        # 列出所有需要在网页上填写的字段
        fields = ['book_id', 'book_name', 'book_isbn', 'book_author', 'book_publisher', 'book_price', 'interviews_times']
        
        # 定义样式，让输入框整齐一点
        widgets = {
            'book_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '最多8位字符'}),
            'book_name': forms.TextInput(attrs={'class': 'form-control'}),
            'book_isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'book_author': forms.TextInput(attrs={'class': 'form-control'}),
            'book_publisher': forms.TextInput(attrs={'class': 'form-control'}),
            'book_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'interviews_times': forms.NumberInput(attrs={'class': 'form-control', 'value': 0}),
        }