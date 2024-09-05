from flask import render_template, request, redirect, url_for, flash, session
from flask import current_app as app
from applications.database import db
from applications.models import User, Admin, BookSection, Book, BookRequest
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import desc



# admin = Admin(username='adminiitm', password='123@adminiitm')  # Use your actual admin username and password
# db.session.add(admin)
# db.session.commit()


@app.route('/')
def home():
    return render_template('home.html')


#logic for signup  for user 
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        #checking if email is taken or not
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Username is already is in use, Please choose a different one.', 'danger')
            return redirect(url_for('signup'))
        if existing_email:
            flash('Email is already in use by a diffrent user', 'danger')
            return redirect(url_for('signup'))

        #password hassing before apending it into database
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        #creating the new user with hashed password 
        new_user = User(username=username, name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


#logic for login of user 
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_instance = User.query.filter_by(username=username).first()

        if user_instance and check_password_hash(user_instance.password, password):
            session['username'] = username
            # Fetch the latest 5 books and 5 sections
            latest_book = Book.query.order_by(Book.id.desc()).limit(5).all()
            latest_section = BookSection.query.order_by(BookSection.id.desc()).limit(5).all()
            # Render the dashboard template with these variables
            return render_template('dashbord.html', name=user_instance.name, latest_book=latest_book, latest_section=latest_section)
        else:
            flash('Either username or password is wrong please try again.', 'danger')
    return render_template('login.html')


#this is for user conviniance so that he can come back to dashbord from anywhere
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        username= session.get('username')
        user = User.query.filter_by(username=username).first()
        latest_book = Book.query.order_by(Book.id.desc()).limit(5).all()
        latest_section = BookSection.query.order_by(BookSection.id.desc()).limit(5).all()
        return render_template('dashbord.html', name=user.name, latest_book=latest_book, latest_section=latest_section)
    else:
        flash('You are not logged in!', 'danger')
        return redirect(url_for('login'))

#logout logic for the user 
@app.route('/logout')
def logout():
    session.pop('username', None) 
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

#all section list for user
@app.route('/user_all_section')
def user_all_section():

    all_section = BookSection.query.order_by(desc(BookSection.id)).all()

    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    return render_template('user_all_section.html' ,  latest_section=all_section, name=user.name)

#all books list for user
@app.route('/user_all_book')
def user_all_book():

    all_book = Book.query.order_by(desc(Book.id)).all()

    username = session.get('username')
    user = User.query.filter_by(username=username).first()

    return render_template('user_all_book.html' , latest_book = all_book , name = user.name)


#this logic wil help user to search books/section on the web app
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    if query:
        matching_books = Book.query.filter(Book.title.contains(query) | Book.author.contains(query)).all()
        matching_sections = BookSection.query.filter(BookSection.title.contains(query)).all()
        username = session.get('username')
        user = User.query.filter_by(username=username).first()
        return render_template('user_search.html', books=matching_books, sections=matching_sections, query=query, name = user.name)
    else:
        flash('Please enter a search term.', 'info')
        return redirect(url_for('dashboard'))  


#this logic is for user to request a book to admin/librarian
@app.route('/request_book/<int:book_id>', methods=['POST'])
def request_book(book_id):
    # Check if user is logged in
    if 'username' not in session:
        flash('You must be logged in to request a book.', 'danger')
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()

    # Limit the number of book requests to 1 at a time
    if user.book_requests.filter_by(status='pending').count() >= 1:
        flash('You cannot request more than 1 book at time once your previus book get acepted/deneyed only after that you can request a new book.', 'danger')
        return redirect(url_for('dashboard'))
    #limit total book should be less than 5
    if user.owned_books.count() >= 5:
        flash('you can not have more than 5 book at a time in library', 'danger')
        return redirect(url_for('dashboard'))

    book = Book.query.get_or_404(book_id)

    # Check if the book is already owned by the user
    if book in user.owned_books:
        flash('You already own this book.', 'danger')
        return redirect(url_for('dashboard'))

    # Check if the book can be requested
    if not book.can_be_requested():
        flash('This book is not available for request.', 'danger')
        return redirect(url_for('dashboard'))

    # Check for duplicate pending request for the same book by the user
    if BookRequest.query.filter_by(user_id=user.id, book_id=book.id, status='pending').first():
        flash('You have already requested this book.', 'warning')
        return redirect(url_for('dashboard'))

    # Add the new book request
    new_request = BookRequest(user_id=user.id, book_id=book.id, status='pending')
    db.session.add(new_request)
    db.session.commit()

    flash('Your request has been submitted.', 'success')
    return redirect(url_for('dashboard'))



#this is to acsses the user libarary
@app.route('/user_library')
def user_library():
    username = session.get('username')
    user = User.query.filter_by(username=username).first()


    return render_template('user_library.html', user=user)



#this logic will help user to return a owend book after reading
@app.route('/return_book/<int:book_id>', methods=['POST'])
def return_book(book_id):
    if 'username' not in session:
        flash('You must be logged in to return a book.', 'danger')
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    
    # Check if the user actually owns the book
    book = Book.query.get(book_id)
    if book not in user.owned_books:
        flash('Could not find the book to return.', 'danger')
        return redirect(url_for('user_library'))
    
    # Remove the book from the user's owned books
    user.owned_books.remove(book)
    
    # Increment the book's quantity since it's being returned
    book.quantity += 1
    
    db.session.commit()

    flash('Book returned successfully. Thank you!', 'success')
    return redirect(url_for('user_library'))



#this is for user can see all of the books of a particular session
@app.route('/user_section_details/<int:section_id>')
def user_section_details(section_id):

    if 'username' not in session:
        flash('You must be logged in to view this page.', 'info')
        return redirect(url_for('login'))

 
    section = BookSection.query.get_or_404(section_id)
    books = section.books.all()
    username = session.get('username')
    user = User.query.filter_by(username=username).first()

    return render_template('user_section_details.html', section=section, books=books, name=user.name)


#this logic is to redirect the user to the cart and if the quantity of book is 0 then it should not redirect anywhere
@app.route('/purchase/<int:book_id>')
def purchase_page(book_id):
    book = Book.query.get_or_404(book_id)
    if book.quantity > 0:
        return render_template('user_cart.html', book=book)
    else:
        flash('This book is currently not available for purchase.', 'info')
        return redirect(url_for('dashboard'))


#this is for after buying the quantity of books should reduce by one  with dummy payment page
@app.route('/confirm_purchase/<int:book_id>')
def confirm_purchase(book_id):
    book = Book.query.get_or_404(book_id)
    

    book.quantity -= 1
    db.session.commit()
    flash('You have successfully purchased {} for 199 rupees.'.format(book.title), 'success')


    return redirect(url_for('dashboard'))


@app.route('/deny_purchase', methods=['POST'])
def deny_purchase():
    flash('Looks like you have changed your mind .', 'info')
    return redirect(url_for('dashboard'))




















#this is the admin login logic
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        #here we are creating admin veriable in that we are storing the username of the admin
        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.password == password:
            session['admin_logged_in'] = True
            session['username'] = username

            #this is for the section created by admin which will show on admin dashboard
            latest_section = BookSection.query.order_by(desc(BookSection.id)).limit(4).all()

            book_requests = BookRequest.query.order_by(BookRequest.requested_on.desc()).all()

            return render_template('admin_dashbord.html', username=admin.username, latest_section=latest_section, book_requests=book_requests)
        else:
            flash('Invalid admin credentials. Please try again.')

    return render_template('admin_login.html')


#this is admin logout logic
@app.route('/admin_logout')
def admin_logout():
    session.pop('username', None)  
    flash('You have been logged out.', 'success')
    return redirect(url_for('admin_login'))


#this is to add new section in the dashboard
@app.route('/admin/add-book-section', methods=['GET', 'POST'])
def add_book_section():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')

        new_section = BookSection(title=title, description=description)
        db.session.add(new_section)
        db.session.commit()
        flash('New book section has been added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('create_section.html')

#this is to redirect admin from anywheree to the admin dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'username' in session:
        latest_section = BookSection.query.order_by(desc(BookSection.id)).limit(4).all()
        
        book_requests = BookRequest.query.order_by(BookRequest.requested_on.desc()).all()

        username = session.get('username')
        admin = Admin.query.filter_by(username=username).first()
        return render_template('admin_dashbord.html', username=admin.username, latest_section=latest_section, book_requests=book_requests)
    else:
        flash('You are not logged in!', 'danger')
        return redirect(url_for('home'))
    


#this logic wil show admin all the avliable section in the web app
@app.route('/all_section')
def all_section():

    all_books = BookSection.query.order_by(desc(BookSection.id)).all()

    username = session.get('username')
    admin = Admin.query.filter_by(username=username).first()
    return render_template('all_section.html' ,  latest_section=all_books, username=admin.username)


#this logic will help admin upload a book 
@app.route('/admin/upload-book', methods=['GET', 'POST'])
def upload_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        quantity = request.form['quantity']
        section_id = request.form['section_id']
        content = request.form['content']
   
        book = Book(title=title, author=author, isbn=isbn, quantity=quantity, section_id=section_id, content=content)


        db.session.add(book)
        db.session.commit()
        
        flash('Book successfully uploaded')
        return redirect(url_for('admin_dashboard'))
    sections = BookSection.query.all()
    return render_template('upload_book.html', sections=sections)


#this will show section details which includes updating the book quantity or detelting the book
@app.route('/section/<int:section_id>', methods=['GET', 'POST'])
def section_detail(section_id):
    section = BookSection.query.get_or_404(section_id)
    if request.method == 'POST':
        # Check if deleting a book
        if 'delete_book' in request.form:
            book_id = request.form.get('delete_book')
            book = Book.query.get(book_id)
            if book:
                db.session.delete(book)
                db.session.commit()
                flash('Book deleted successfully.', 'success')
        # Check if updating quantity
        elif 'update_quantity' in request.form:
            book_id = request.form.get('book_id')
            quantity = request.form.get('quantity')
            book = Book.query.get(book_id)
            if book:
                book.quantity = quantity
                db.session.commit()
                flash('Book quantity updated successfully.', 'success')
                
    books = Book.query.filter_by(section_id=section_id).all()
    username = session.get('username')
    admin = Admin.query.filter_by(username=username).first()
    return render_template('section_detail.html', section=section, books=books, username=admin.username)


#this will search book/section in admin profile wich will help admin 
@app.route('/admin_search')
def admin_search():
    query = request.args.get('query', '')
    if query:
        matching_books = Book.query.filter(Book.title.contains(query) | Book.author.contains(query)).all()
        matching_sections = BookSection.query.filter(BookSection.title.contains(query)).all()
        username = session.get('username')
        admin = Admin.query.filter_by(username=username).first()
        return render_template('admin_search.html', books=matching_books, sections=matching_sections, query=query, username=admin.username)
    else:
        flash('Please enter a search term.', 'info')
        return redirect(url_for('admin_dashboard'))  
    




#this logic is when a user request a book and admin do not want to acept the request he can deny it
@app.route('/deny_book_request/<int:request_id>')
def deny_book_request(request_id):
    book_request = BookRequest.query.get_or_404(request_id)
    

    db.session.delete(book_request)
    db.session.commit()
    
    flash('Book request denied.', 'danger')
    return redirect(url_for('admin_dashboard'))


#this is for when admin wants to give a specific book to user
@app.route('/accept_book_request/<int:request_id>')
def accept_book_request(request_id):
    book_request = BookRequest.query.get_or_404(request_id)
    book = book_request.book
    
    if book.quantity > 0:
        book.quantity -= 1  
        user = book_request.user
        user.owned_books.append(book)  
        db.session.delete(book_request) 
        
        db.session.commit()
        flash('Book request accepted. The book has been added to the user\'s library.', 'success')
    else:
        flash('This book is no longer available.', 'danger')
    
    return redirect(url_for('admin_dashboard'))


#this logic will help admin manage sections this will help in deleting the particular section 
@app.route('/delete_section/<int:section_id>', methods=['POST'])
def delete_section(section_id):
    if 'username' not in session:  
        flash("You must be logged in as an admin to perform this action.", "danger")
        return redirect(url_for('admin_login'))

    section = BookSection.query.get_or_404(section_id)
    # when admin delete a section all the book related to taht section will have none value in plae of section id 
    books = Book.query.filter_by(section_id=section.id).all()
    for book in books:
        book.section_id = None
    db.session.delete(section)
    db.session.commit()

    flash('Section has been deleted and all the associated books of section has now no section assigne.', 'success')
    return redirect(url_for('all_section'))


#this logic will help admin manage the library in more clean way
@app.route('/admin/stats')
def admin_stats():
    if 'username' not in session:  
        flash("You must be logged in as an admin to view this page.", "danger")
        return redirect(url_for('admin_login'))

    total_users = User.query.count()
    total_sections = BookSection.query.count()
    total_books = Book.query.count()

    username = session.get('username')
    admin = Admin.query.filter_by(username=username).first()

    return render_template('admin_stats.html', username=admin.username, total_users=total_users, total_sections=total_sections,  total_books=total_books)

                           

#this will show list of all the books in the app after admin go to stat/all_the_books
@app.route('/admin_all_book', methods=['GET', 'POST'])
def admin_all_book():
    if 'username' not in session:
        flash("You must be logged in as an admin to view this app", "danger")
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        # Check if deleting a book
        if 'delete_book' in request.form:
            book_id = request.form.get('delete_book')
            book = Book.query.get(book_id)
            if book:
                db.session.delete(book)
                db.session.commit()
                flash('Book deleted successfully.', 'success')
        # Check if updating quantity
        elif 'update_quantity' in request.form:
            book_id = request.form.get('book_id')
            quantity = request.form.get('quantity')
            book = Book.query.get(book_id)
            if book:
                book.quantity = quantity
                db.session.commit()
                flash('Book quantity updated successfully.', 'success')
                
    username = session.get('username')
    admin = Admin.query.filter_by(username=username).first()
    
    books = Book.query.all()
    return render_template('admin_all_book.html', books=books, username=admin.username)

#this logic wil show how many users are present on the app
@app.route('/all_user', methods=['GET','POST'])
def all_user():
    if 'username' not in session:
        flash("you must logged in as admin to view this page", "danger")
        return redirect(url_for('admin_login'))
    
    if 'remove_user' in request.form:
        user_id = request.form['remove_user']
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            flash('user has been removed successsfully.', 'success')

    username = session.get('username')
    admin = Admin.query.filter_by(username=username).first()

    user= User.query.order_by(desc(User.id)).all()
    return render_template('all_user.html', user=user, username=admin.username)


#this will show all the books present at the specific user library
@app.route('/admin_user_books/<int:user_id>')
def admin_user_books(user_id):
    if 'username' not in session or not Admin.query.filter_by(username=session['username']).first():
        flash("You must be logged in as admin to view this page", "danger")
        return redirect(url_for('admin_login'))

    user = User.query.get_or_404(user_id)
    books = user.owned_books.all()
    username = session.get('username')
    admin = Admin.query.filter_by(username=username).first()
    return render_template('admin_user_book.html', books=books, user=user, username=admin.username)



#this logic can help admin remove a book from any user library 
@app.route('/remove_book_from_user_library/<int:user_id>/<int:book_id>', methods=['POST'])
def remove_book_from_user_library(user_id, book_id):
    if 'username' not in session or not Admin.query.filter_by(username=session['username']).first():
        flash("You must be logged in as admin to perform this action.", "danger")
        return redirect(url_for('admin_login'))

    # Retrieve the user and the book instances
    user = User.query.get_or_404(user_id)
    book = Book.query.get_or_404(book_id)

    # Remove the book from the user's library
    if book in user.owned_books:
        user.owned_books.remove(book)
        book.quantity += 1
        db.session.commit()
        flash(f"The book '{book.title}' has been removed from {user.name}'s library.", 'success')
    else:
        flash("The book could not be found in the user's library.", 'danger')

    return redirect(url_for('admin_user_books', user_id=user_id))


#all the books with no section alloted
@app.route('/books_with_no_section', methods=['GET', 'POST'])  
def books_with_no_section():
    # Check if the user is logged in as an admin
    if 'username' not in session:
        flash("You must be logged in as admin to perform this action.", "danger")
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        # Handling book deletion
        if 'delete_book' in request.form:
            book_id = request.form.get('delete_book')
            book = Book.query.get(book_id)
            if book:
                db.session.delete(book)
                db.session.commit()
                flash('Book has been deleted successfully.', 'success')

        # Handling book quantity update
        elif 'update_quantity' in request.form:
            book_id = request.form.get('book_id')
            quantity = request.form.get('quantity', type=int)  
            book = Book.query.get(book_id)
            if book:
                book.quantity = quantity
                db.session.commit()
                flash('Book quantity updated successfully.', 'success')

    books_without_section = Book.query.filter(Book.section_id.is_(None)).all()  
    admin_username = session.get('username')
    admin = Admin.query.filter_by(username=admin_username).first() if admin_username else None
    all_sections = BookSection.query.all()

    return render_template('book_no_section.html', books=books_without_section, username=admin.username, all_sections=all_sections)


#this wil help admin to assinge a no section book to a specific section
@app.route('/assign_section_to_book', methods=['POST'])
def assign_section_to_book():
    if 'username' not in session:
        flash("You must be logged in as admin to perform this action.", "danger")
        return redirect(url_for('admin_login'))
    
    book_id = request.form.get('book_id')
    section_id = request.form.get('section_id')
    book = Book.query.get(book_id)
    if book and section_id:
        book.section_id = section_id
        db.session.commit()
        flash('Book has been assigned to the section successfully.', 'success')
    else:
        flash('Failed to assign the book to the section.', 'danger')
    
    return redirect(url_for('books_with_no_section'))


#this will help admin go to edit page of a section
@app.route('/edit_section/<int:section_id>', methods=['GET'])
def edit_section(section_id):
    section = BookSection.query.get_or_404(section_id)
    return render_template('edit_section.html', section=section, section_id=section_id)


#this will help admin edit a section
@app.route('/update_section/<int:section_id>', methods=['POST'])
def update_section(section_id):
    section = BookSection.query.get_or_404(section_id)
    section.title = request.form['title']
    section.description = request.form['description']
    db.session.commit()
    flash('Section updated successfully.', 'success')
    return redirect(url_for('all_section'))


@app.route('/reset')
def reset():
    return redirect(url_for('admin_login'))


#this will help admin edit a book
@app.route('/update_book/<int:book_id>', methods=['GET', 'POST'])
def update_book(book_id):
    # Get the book from the database
    book = Book.query.get_or_404(book_id)

    if request.method == 'POST':
        # Get form data
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        quantity = request.form['quantity']
        section_id = request.form.get('section_id')  
        content = request.form['content']

        # Update book details
        book.title = title
        book.author = author
        book.isbn = isbn
        book.quantity = quantity
        book.section_id = None if section_id == '' else section_id  
        book.content = content

        # Save the changes
        db.session.commit()

        
        flash('Book updated successfully', 'success')
        return redirect(url_for('admin_dashboard'))

 
    sections = BookSection.query.all()
    return render_template('edit_book.html', book=book, sections=sections)




