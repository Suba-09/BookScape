import requests
import pymysql
import pandas as pd

def check_bookdata(database,table_name,category):
    try:
        print("Establishing the sql  connection")
        mydb = pymysql.connect(
            host="localhost",
            user="root",
            password="123456789$$"
        )

        # Creating a cursor to execute queries
        mycursor = mydb.cursor()

        # Fetching the list of databases
        mycursor.execute("SHOW DATABASES")
        databases = [x[0] for x in mycursor.fetchall()]

        # Delete the database if it exists
        if database not in databases:
            return False
        

        # Using the newly created database
        mycursor.execute("USE " + database)
        mycursor.execute("SELECT DATABASE()")
        current_db = mycursor.fetchone()[0]
        
        check_query = f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s AND table_name = %s"
        mycursor.execute(check_query,(database, table_name))

        if mycursor.fetchone()[0]==0:
            return False
        
        check_query = f"SELECT COUNT(*) FROM {table_name} WHERE search_key = %s"
        mycursor.execute(check_query,(category))
        
        if mycursor.fetchone()[0]==0:
            return False
        return True
    except pymysql.connector.Error as err:
        return (f"Error: {err}") 
    finally:
        # Close the cursor and connection
        if mycursor:
            mycursor.close()
        if mydb:
            mydb.close()

def scrap_book_data(api_key, api_url, query, total_books, max_results):
  """ 
    Scrapes book data from the given API.

    Parameters:
    api_key (str): API key for authentication.
    api_url (str): URL of the API endpoint.
    query (str): Search query.
    total_books (int): Total number of books to fetch.
    max_results (int): Maximum number of books per API request.

    Returns:
    list(list,bool): A list of all scrapped book data, bool that indicated whether the api key limit has exceeded or not
  """  
  scrapped_books_data=[]
  print("Started to scrap the book of type '"+query+"'")
  for start_index in range(0, total_books, max_results):
    # Make the API request
    response = requests.get(
        api_url,
        params = {
            "key": api_key,
            "q": query,
            "startIndex": start_index,
            "maxResults": max_results
        }
    )
    api_keyLimit_exceded = True
    if response.status_code == 200:
        print("----------------------")
        api_keyLimit_exceded = False
        # Parse the response to JSON
        scrapped_volume_data = response.json()
        # Extract books from the response    
        for books in scrapped_volume_data.get('items',[]):
            scrapped_books_data.append(books)
        print(f"Scrapped {len(scrapped_books_data)} books")    

  return [scrapped_books_data,api_keyLimit_exceded]
  
def process_books_data(scrapped_books_data, query):
    """
    Processes the raw book data to extract relevant information.

    Parameters:
        scrapped_books_data (List[Dict]): books from the API response.
        query (str): The search query used.

    Returns:
        List[Dict]: A list of processed book data dictionaries.
    """
    books_data=[]
    seen_ids = set()
    for books in scrapped_books_data:
        book={}
        book['book_id']=books['id']
        if book['book_id'] not in seen_ids:
            seen_ids.add(book['book_id'])
            book['search_key']=query
            book['book_title'] = books.get('volumeInfo',{}).get('title','N/A')
            book['book_subtitle'] = books.get('volumeInfo',{}).get('subtitle','N/A')
            book['book_authors'] = books.get('volumeInfo',{}).get('authors',[])
            book['book_description'] = books.get('volumeInfo',{}).get('description','N/A')
            book['industryIdentifiers'] = books.get('volumeInfo',{}).get('industryIdentifiers',[])
            book['text_readingModes'] = books.get('volumeInfo',{}).get('readingModes',{}).get('text','0')
            book['image_readingModes'] = books.get('volumeInfo',{}).get('readingModes',{}).get('image','0')
            book['pageCount'] = books.get('volumeInfo',{}).get('pageCount','')
            book['categories'] = books.get('volumeInfo',{}).get('categories',[])
            book['language'] = books.get('volumeInfo',{}).get('language','N/A')
            book['imageLinks'] = books.get('volumeInfo',{}).get('imageLinks',{})
            book['ratingsCount'] = books.get('volumeInfo',{}).get('ratingsCount',0)
            book['averageRating'] = books.get('volumeInfo',{}).get('averageRating',0)
            book['country'] = books.get('saleInfo',{}).get('country','N/A')
            book['saleability'] = books.get('saleInfo',{}).get('saleability','N/A')
            book['isEbook'] = books.get('saleInfo',{}).get('isEbook','0')
            book['amount_listPrice'] = books.get('saleInfo',{}).get('listPrice',{}).get('amount',0)
            book['currencyCode_listPrice'] = books.get('saleInfo',{}).get('listPrice',{}).get('currencyCode','N/A')
            book['amount_retailPrice'] = books.get('saleInfo',{}).get('retailPrice',{}).get('amount',0)
            book['currencyCode_retailPrice'] = books.get('saleInfo',{}).get('retailPrice',{}).get('currencyCode','N/A')
            book['buyLink'] = books.get('saleInfo',{}).get('buylink','')
            publishedDate = books.get('volumeInfo',{}).get('publishedDate','').split('-')
            book['year'] = ''
            for part in (publishedDate[0], publishedDate[-1]):
                if len(part) == 4 and part.isdigit():
                    book['year'] = part
                    break
                    
            book['publisher'] = books.get('volumeInfo',{}).get('publisher','')

            # Flatten nested dictionaries/lists into strings (if needed)
            book['book_authors'] = ', '.join(book['book_authors']) if isinstance(book['book_authors'], list) else book['book_authors']
            if book['industryIdentifiers']:  # If the list is not empty
                book['industryIdentifiers'] = ', '.join([identifier.get('identifier', '') for identifier in book['industryIdentifiers'] if 'identifier' in identifier])
            else:  # If the list is empty
                book['industryIdentifiers'] = ''
            book['categories'] = ', '.join(book['categories']) if isinstance(book['categories'], list) else book['categories']
            book['imageLinks'] = str(book['imageLinks'])

            books_data.append(book)
    print(f"processed {len(books_data)} books")
    return books_data

def create_and_insert_books(database,table, books_list):
    """
    Create database and store the processed book data

    Parameters:
        books_list (List[Dict]): processed book list from the API response.
        database (str): The Database used to store books.

    Returns:
        nothing
    """    
    try:
        print("Establishing the sql  connection")
        mydb = pymysql.connect(
            host="localhost",
            user="root",
            password="123456789$$"
        )

        # Creating a cursor to execute queries
        mycursor = mydb.cursor()

        # Fetching the list of databases
        mycursor.execute("SHOW DATABASES")
        databases = [x[0] for x in mycursor.fetchall()]

        # Delete the database if it exists
        if database not in databases:
            print("Creating a new database " + database)
            mycursor.execute("CREATE DATABASE " + database)

        # Using the newly created database
        mycursor.execute("USE " + database)
        mycursor.execute("SELECT DATABASE()")
        current_db = mycursor.fetchone()[0]
        print(f"Currently using database: {current_db}")

        # Create table query
        table_creation_query = f"""
        CREATE TABLE IF NOT EXISTS {table}  (
            book_id VARCHAR(255) PRIMARY KEY,
            search_key VARCHAR(255),
            book_title VARCHAR(255),
            book_subtitle TEXT,
            book_authors TEXT,
            book_description TEXT,
            industryIdentifiers TEXT,
            text_readingModes BOOLEAN,
            image_readingModes BOOLEAN,
            pageCount INT,
            categories TEXT,
            language VARCHAR(10),
            imageLinks TEXT,
            ratingsCount INT,
            averageRating DECIMAL(3,2),
            country VARCHAR(10),
            saleability VARCHAR(50),
            isEbook BOOLEAN,
            amount_listPrice DECIMAL(10,2),
            currencyCode_listPrice VARCHAR(10),
            amount_retailPrice DECIMAL(10,2),
            currencyCode_retailPrice VARCHAR(10),
            buyLink TEXT,
            year TEXT,
            publisher TEXT
        )
        """
        
        # Execute the query to create the table
        mycursor.execute(table_creation_query)

        # Prepare list for batch insert
        books_data = []
        for book in books_list:
            data = (
                book['book_id'],
                book['search_key'],
                book['book_title'],
                book['book_subtitle'],
                book['book_authors'],
                book['book_description'],
                book['industryIdentifiers'],
                book['text_readingModes'],
                book['image_readingModes'],
                book['pageCount'],
                book['categories'],
                book['language'],
                book['imageLinks'],
                book['ratingsCount'],
                book['averageRating'],
                book['country'],
                book['saleability'],
                book['isEbook'],
                book['amount_listPrice'],
                book['currencyCode_listPrice'],
                book['amount_retailPrice'],
                book['currencyCode_retailPrice'],
                book['buyLink'],
                book['year'],
                book['publisher']
            )
            books_data.append(data)

        # SQL query for inserting data
        insert_query = """
           INSERT IGNORE INTO books(
            book_id, search_key, book_title, book_subtitle, book_authors, book_description, 
            industryIdentifiers, text_readingModes, image_readingModes, pageCount, categories, language, 
            imageLinks, ratingsCount, averageRating, country, saleability, isEbook, amount_listPrice, 
            currencyCode_listPrice, amount_retailPrice, currencyCode_retailPrice, buyLink, year, publisher
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Insert data using executemany for batch processing
        mycursor.executemany(insert_query, books_data)

        # Commit the transaction
        mydb.commit()

        # Print success message
        return (f"{mycursor.rowcount} records inserted successfully!")

    except pymysql.connector.Error as err:
        return (f"Error: {err}")
    finally:
        # Close the cursor and connection
        if mycursor:
            mycursor.close()
        if mydb:
            mydb.close()

  
# api_key='AIzaSyBtsFOoea0HRJ5BMki1IPGgN9MRvPwlpe8'
# api_url='https://www.googleapis.com/books/v1/volumes'
# book_category = 'novel'
# scrapped_books_data = scrap_book_data(api_key, api_url, book_category, 1000, 40)[0]
# processed_books_data = process_books_data(scrapped_books_data, book_category)
# create_and_insert_books('scrappedbooks','books',processed_books_data)




       











