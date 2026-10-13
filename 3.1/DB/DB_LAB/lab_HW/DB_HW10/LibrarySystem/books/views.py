from django.shortcuts import render, redirect, get_object_or_404

from .models import Book
from .forms import BookForm
from django.db.models import Q

# 1. 首页：只展示图书数量
def index(request):
    book_count = Book.objects.count()
    return render(request, 'books/index.html', {'book_count': book_count})

# 2. 图书列表
def book_list(request):
    query = request.GET.get('q', '').strip()
    books = Book.objects.all().order_by('book_id')
    if query:
        books = books.filter(
            Q(book_id__icontains=query) |
            Q(book_name__icontains=query) |
            Q(book_author__icontains=query) |
            Q(book_publisher__icontains=query) |
            Q(book_isbn__icontains=query)
        )
    return render(request, 'books/book_list.html', {'books': books, 'q': query})

# 3. 添加图书
def book_create(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'books/book_form.html', {'form': form, 'title': '添加图书'})

# 4. 修改图书
def book_update(request, pk):
    # 注意：因为你的PK是char类型，这里的pk参数能正确接收字符串
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('book_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'books/book_form.html', {'form': form, 'title': '修改图书'})

# 5. 删除图书
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        return redirect('book_list')
    return render(request, 'books/book_confirm_delete.html', {'book': book})