import streamlit as st
import pymysql
import pandas as pd
from scrap_and_store_books import scrap_book_data,process_books_data,create_and_insert_books,check_bookdata
from query_dictionary import get_FAQ, get_axis

# Database connection
def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="scrappedbooks",
        charset="utf8mb4"
    )

# Query execution
def run_query(query, params=None):
    connection = get_connection()
    try:
        df = pd.read_sql(query, connection, params=params)
        return df
    finally:
        connection.close()

def display_home_page():
    """
    Function to display the home page of the Streamlit application.
    """
    st.markdown(
        """
        ## 📖 About This App
        """
        )
    st.markdown("""
        Welcome to the **Bookscape Explorer - A Book Data Analysis Application**!  
        This app allows you to:
        - Scrap data from Google books of your favourite Category       
        - Search for and explore books.
        - Analyze book data.
        
        **Get started by selecting a feature from the Navigator!**
    """)    
       
    # About the Dataset Section
    st.header("📊 About the Dataset")
    st.markdown("""
    The book data is extracted from public APIs and includes information such as:
    - Titles, authors, and descriptions.
    - Ratings, reviews, and prices.
    - Categories, publishers, and publication years.
    """)


def display_extract_page():
    """
    function to display Extract Page
    """
    options=['','Classics','Romance','Health','Food','Crime','Maths','Science','Novel','Fantacy','Poetry','Art','sports','Travel']
    category = st.selectbox("Select a category to extract books", options)
    if(st.button("Extact books")):
        if(category):
            message = check_bookdata('scrappedbooks','books',category)
            if(message):
                st.write(f"The Books category '{category}' is already extracted")
            else:
                st.write(f"Initiating to extract books of category {category}")
                st.write('started to extract books')
                api_key=''
                api_url='https://www.googleapis.com/books/v1/volumes'
                scrapped_data = scrap_book_data(api_key, api_url, category, 1000, 40)
                processed_books_data = process_books_data(scrapped_data[0], category)
                if scrapped_data[1]:
                    st.write("The api key limit has exceeded.You cannot scrap books today.")
                else:                    
                    st.write(f"Scrapped {len(scrapped_data[0])} books")
                    message = create_and_insert_books('scrappedbooks','books',processed_books_data)            
                    st.write(message)

                
        else:
            st.warning('Select a book category to start the extraction')

def display_search_page():
    """
    Function to display Search page
    """
    st.sidebar.header("Explore Books")
    title_filter = st.sidebar.text_input("Title")
    publisher_filter = st.sidebar.text_input("Publisher")
    min_rating = st.sidebar.slider("Minimum Rating", 0.0, 5.0, 0.0,0.1)
    max_rating = st.sidebar.slider("Maximum Rating", 0.0, 5.0, 5.0,0.1)
    price_ranges = ["","less than 500", "500 - 1000", "1000 - 2000", "2000 and above"]
    price_filter = st.sidebar.selectbox("Price Range",price_ranges,placeholder="select a price range")

    # Dynamic Query Construction
    selectQuery=" SELECT book_title, book_authors "
    tableQuery = " FROM Books "
    whereQuery=" where averageRating BETWEEN %s AND %s"
    params=[min_rating,max_rating]
    if min_rating != 0.0 or max_rating != 5.0:
       selectQuery+=", averageRating"
    if title_filter:
        whereQuery += " AND book_title LIKE %s"
        params.append(f"%{title_filter}%")
    if publisher_filter:
        selectQuery+=", publisher"
        whereQuery += " AND publisher LIKE %s"
        params.append(f"%{publisher_filter}%")
    if price_filter:
        selected_index = price_ranges.index(price_filter)
        selectQuery+=", amount_retailprice"
        match selected_index:
            case 1:
                whereQuery += " AND amount_retailprice BETWEEN %s AND %s"
                params.extend([0,500])
            case 2:
                whereQuery += " AND amount_retailprice BETWEEN %s AND %s"
                params.extend([500,1000])
            case 3:
                whereQuery += " AND amount_retailprice BETWEEN %s AND %s"
                params.extend([500,1000])
            case 4:
                whereQuery += " AND amount_retailprice >= %s"
                params.append(2000)
            case _:
                whereQuery += " "
    query = selectQuery + tableQuery + whereQuery 

    st.header("Book Details")
    df1 = run_query(query,params)     
    if not df1.empty:
        st.dataframe(df1)
    else:
        st.write("No results found!")
        
def display_analyse_page():    
    """
    Function to display Analyse page
    """
    st.sidebar.header("Frequently used Queries")
    faqDict = get_FAQ()
    queryList=list(faqDict.keys())
    axisList = get_axis()
    faqQuery = st.sidebar.selectbox("Select a Query", queryList, placeholder="select a query")
    if faqQuery:
        index = queryList.index(faqQuery)
        st.header("FAQ Query Results")
        query = faqDict[faqQuery]
        df = run_query(query)
        if not df.empty:
            st.dataframe(df)
            if(axisList[index] != ""):
                st.bar_chart(df.set_index(axisList[index]))            
        else:
            st.write("No results found!")    
    else:
        st.warning("Select a query to view the insigts of the data")



# Streamlit app
def main():
    st.markdown(
    """
    <h1 style='
    text-align: center; 
    background-color: lightblue; 
    padding: 20px; 
    border-radius: 10px;'>
    📚 Bookscape Explorer </h1>
    """,unsafe_allow_html=True
    )
    menu = ["Home", "Extract Books", "Search Books", "Analyse Books"]
    choice = st.sidebar.selectbox("Navigate", menu)
    if choice==menu[0]:
        display_home_page()
    if choice== menu[1]:
        display_extract_page()
    if choice== menu[2]:
        display_search_page()
    if choice== menu[3]:
        display_analyse_page()


if __name__ == "__main__":
    main()
