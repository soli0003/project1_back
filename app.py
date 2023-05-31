from datetime import datetime, date, timedelta
import json
from flask import Flask, jsonify, request
from sqlalchemy import desc
from conf import app, db, Book, Customer, Loan
from flask_cors import CORS

CORS(app)


#-------------------------------------------------------------------------------------Display all Undeleted books ----------------------------------------------------------------------------------------

def is_book_loaned(book_id):
    loan = Loan.query.filter_by(book_id=book_id).order_by(desc(Loan.id)).first()
    return loan is not None and loan.return_date is None



@app.route("/showbooks", methods=['GET','POST'])
def show_all_books():
    books_list = [book.to_dict() for book in Book.query.filter(Book.book_deleted == False)]
    for book in books_list:
        book['status'] = 'Loaned' if is_book_loaned(book['id']) else 'Available'
    json_data = json.dumps(books_list)
    return json_data


#-------------------------------------------------------------------------------------Display all Deleted books ----------------------------------------------------------------------------------------

@app.route("/showDeletedbooks", methods=['GET'])
def show_Deleted_books():
    books_list = [book.to_dict() for book in Book.query.filter(Book.book_deleted == True)]
    json_data = json.dumps(books_list)
    return json_data


    
#-------------------------------------------------------------------------------------Display all active customers ----------------------------------------------------------------------------------------

@app.route("/showcustomers", methods=['GET','POST'])
def show_all_customers():
    customers_list = [customer.to_dict() for customer in Customer.query.filter(Customer.active == True)]
    json_data = json.dumps(customers_list)
    # print(json_data)
    return json_data


#-------------------------------------------------------------------------------------Display all deleted customers ----------------------------------------------------------------------------------------

@app.route("/showdeletedcustomers", methods=['GET','POST'])
def show_deleted_customers():
    customers_list = [customer.to_dict() for customer in Customer.query.filter(Customer.active == False)]
    json_data = json.dumps(customers_list)
    # print(json_data)
    return json_data


#-------------------------------------------------------------------------------------Display all active loans ----------------------------------------------------------------------------------------

@app.route("/showactiveloans")
def show_all_loans():
    loans_list = []
    active_loans = Loan.query.filter(Loan.return_date == None).all()
    for loan in active_loans:
        loan_dict = loan.to_dict()
        loan_dict['loan_date'] = loan_dict['loan_date'].strftime('%Y-%m-%d')
        loan_dict['book_name'] = loan.book.name
        loan_dict['identification_number'] = loan.customer.identification_number
        loan_dict['customer_name'] = loan.customer.name
        loans_list.append(loan_dict)
    json_data = json.dumps(loans_list)
    return json_data


#-------------------------------------------------------------------------------------Display all old loans ----------------------------------------------------------------------------------------

@app.route("/showoldloans")
def show_old_loans():
    old_loans_list = []
    old_loans = Loan.query.filter(Loan.return_date != None).all()
    
    for old_loan in old_loans:
        old_loan_dict = old_loan.to_dict()
        old_loan_dict['loan_date'] = old_loan_dict['loan_date'].strftime('%Y-%m-%d')
        old_loan_dict['book_name'] = old_loan.book.name
        old_loan_dict['identification_number'] = old_loan.customer.identification_number
        old_loan_dict['customer_name'] = old_loan.customer.name
        old_loan_dict['return_date'] = old_loan_dict['return_date'].strftime('%Y-%m-%d')
        old_loans_list.append(old_loan_dict)
        
    return jsonify(old_loans_list)
#-------------------------------------------------------------------------------------Display Late loans ----------------------------------------------------------------------------------------

@app.route("/showlateloans")
def show_Late_loans():
    Late_loans_list = []
    current_date = datetime.today().date()
    late_loans = Loan.query.filter(Loan.return_date.is_(None)).all()

    for late_loan in late_loans:
        late_loan_dict = late_loan.to_dict()
        late_loan_dict['loan_date'] = late_loan_dict['loan_date'].strftime('%Y-%m-%d')
        late_loan_dict['book_name'] = late_loan.book.name
        late_loan_dict['identification_number'] = late_loan.customer.identification_number
        late_loan_dict['customer_name'] = late_loan.customer.name
        late_loan_dict['return_date'] = 'Not returned yet'

        book_type = late_loan.book.book_type
        loan_date = late_loan.loan_date
        max_loan_duration = get_max_loan_duration(book_type)
        late_duration = calculate_late_duration(loan_date, current_date, max_loan_duration)

        if late_duration > 0:
            late_loan_dict['late_duration'] = late_duration
            Late_loans_list.append(late_loan_dict)

    return jsonify(Late_loans_list)





def get_max_loan_duration(book_type):
    if book_type == 1:
        return 10
    elif book_type == 2:
        return 5
    elif book_type == 3:
        return 2
    else:
        return 0



def calculate_late_duration(loan_date, return_date, max_loan_duration):
    if return_date is None:
        return_date = date.today()
    loan_date_str = loan_date.strftime('%Y-%m-%d')
    return_date_str = return_date.strftime('%Y-%m-%d')
    loan_date = datetime.strptime(loan_date_str, '%Y-%m-%d')
    return_date = datetime.strptime(return_date_str, '%Y-%m-%d')
    duration = return_date - loan_date
    late_duration = max(0, duration.days - max_loan_duration)
    return late_duration





#-------------------------------------------------------------------------------------search book by name ----------------------------------------------------------------------------------------

@app.route('/searchbooks')
def search():
    search_query = request.args.get('search_query')
    if not search_query:
        return jsonify({'error': 'Missing search query'})

    # return the books that match the search query and are not currently on loan
    books = Book.query.filter(
          (Book.loan_active == False) &
          ((Book.name.ilike(f'%{search_query}%')) |
          (Book.author.ilike(f'%{search_query}%')) |
          (Book.year_published.ilike(f'%{search_query}%')) |
          (Book.book_type.ilike(f'%{search_query}%')))
    ).all()

    # convert books to a list of dictionaries and include loan_active status
    books_data = []
    for book in books:
        book_data = book.to_dict()
        book_data['loan_active'] = book.loan_active
        books_data.append(book_data)

    return jsonify(books_data)


#-------------------------------------------------------------------------------------search customer by name ----------------------------------------------------------------------------------------

@app.route("/searchcustomerbyname")
def search_customer_by_name():
    search_customer_name = [customer_name.to_dict() for customer_name in Customer.query.filter(Customer.name == Customer.name).all()]
    json_data = json.dumps(search_customer_name)
    return json_data


#-------------------------------------------------------------------------------------Add new Customer ----------------------------------------------------------------------------------------

@app.route('/newcustomer', methods=['POST'])
def newcustomer():
    data = request.get_json()
    app.logger.info(data)
    identification_number = data['identification_number']
    name = data['name']
    email = data['email']
    phone = data['phone']
    city = data['city']
    age = data['age']

    

    # Check if identification number is incorrect
    if not identification_number_check(identification_number):
        return "Identification number should have 9 digits"

    # Check if identification number already exists
    existing_customer = Customer.query.filter_by(identification_number=identification_number).first()
    if existing_customer:
        return "Identification number already exists in the system."

    new_customer = Customer(identification_number, name, email, phone, city, age, active=True)
    db.session.add(new_customer)
    db.session.commit()
    return "A new Customer was added."


def identification_number_check(input_id):
        id = str(input_id).strip()
        if len(id) != 9:
            return False
        return True


#-------------------------------------------------------------------------------------Remove a book ----------------------------------------------------------------------------------------
@app.route('/removebook/<id>', methods=['PUT'])
def remove_book(id):
    book = Book.query.filter_by(id=id).first()
    

    book.book_deleted = True
    db.session.commit()

    return 'Book deleted.'




#-------------------------------------------------------------------------------------Remove a customer ----------------------------------------------------------------------------------------
@app.route('/removecustomer/<identification_number>', methods=['PUT'])
def remove_customer(identification_number):

    # Find the customer by identification number
    customer = Customer.query.filter_by(identification_number=identification_number).first()
    if not customer:
        return "Customer not found."
    
    # Check if the customer has any active loans
    active_loans = Loan.query.filter_by(cust_id=customer.id).filter_by(return_date=None).all()
    if active_loans:
        return "Cannot remove customer, They have a book on loan."

    customer.active = False
    db.session.commit()

    return "Customer deleted successfully."






#-------------------------------------------------------------------------------------Add a new book ----------------------------------------------------------------------------------------


@app.route('/newbook', methods=['POST'])
def newbook():
    data = request.get_json()
    # print(data)
    name = data['name']
    author = data['author']
    year_published = data['year_published']
    book_type = data['book_type']

    new_book = Book(name, author, year_published, book_type, loan_active=False, book_deleted=False)
    db.session.add(new_book)
    db.session.commit()
    return "New book added successfully."




#-------------------------------------------------------------------------------------Loan a book----------------------------------------------------------------------------------------


@app.route('/loanbook', methods=['GET','POST'])
def loan_book():
    data = request.get_json()
    identification_number = data['identification_number']
    book_name = data['book_name']
    book_id = data['book_id']
    loan_date = datetime.strptime(data['loan_date'], '%Y-%m-%d')

    
    # Check if identification number is incorrect
    if not identification_number_check(identification_number):
        return "cant find Identification number in the system"
    
    # Check if the customer and book exist
    customer = Customer.query.filter_by(identification_number=identification_number).first()
    book = Book.query.filter_by(name=book_name).first()

    if not customer or not book:
        return 'Invalid customer or book.'

    cust_id = customer.id
    book_id = book.id

    # Check if book is deleted
    if Book.book_deleted == True:
        return "Book does not exist. Please check book ID."

    # Check if book is available to loan
    if book.loan_active:
        return "Book is currently on loan."

    # If the book is available to loan, change to unavailable
    book.loan_active = True

    # Create a new loan record
    new_loan = Loan(cust_id=cust_id, book_id=book_id, loan_date=loan_date, return_date=None)
    db.session.add(new_loan)
    db.session.commit()

    return "Loan successful."



#-------------------------------------------------------------------------------------return a book----------------------------------------------------------------------------------------

@app.route('/returnbook', methods=['POST'])
def return_book():
    data = request.get_json()
    id = data['id']
    cust_id = data['cust_id']
    book_id = data['book_id']
    return_date = datetime.strptime(data['return_date'], '%Y-%m-%d')

    # Retrieve the existing loan record
    loan = Loan.query.filter_by(id=id, cust_id=cust_id, book_id=book_id).first()

    if not loan:
        return 'No loan record found for the given customer and book.'

    if loan.return_date is not None:
        return "Book already returned, try a different ID number."

    # Retrieve the book instance
    book = Book.query.get(book_id)

    # Convert loan_date to datetime type. Check if return date is greater than loan date
    return_date = datetime.combine(loan.loan_date, datetime.min.time())
   

    # Change the book status from unavailable to available
    book.loan_active = False

    # Update the return_date
    loan.return_date = return_date
    db.session.commit()

    return 'Book returned successfully.'




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
