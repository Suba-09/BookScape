def get_FAQ():
    faq_queries = {
    "":"",
    "1.Check Availability of eBooks vs Physical Books": """
        SELECT 
            CASE
                WHEN isEbook = TRUE THEN 'eBook'
                ELSE 'Physical Book'
            END AS book_type,
            COUNT(*) AS "Count"
        FROM books
        GROUP BY isEbook;
    """,
    "2.Find the Publisher with the Most Books Published": """
        SELECT 
            publisher, 
            COUNT(*) AS total_books
        FROM books 
        WHERE publisher IS NOT NULL AND publisher != ''
        GROUP BY publisher
        ORDER BY total_books DESC LIMIT 1;
    """,
    "3.Identify the Publisher with the Highest Average Rating": """
        SELECT 
            publisher, 
            MAX(averageRating) AS avge 
        FROM books 
        WHERE publisher IS NOT NULL AND publisher != ''
        GROUP BY publisher 
        ORDER BY avge DESC LIMIT 1;
    """,
    "4.Get the Top 5 Most Expensive Books by Retail Price": """
        SELECT 
            book_title,
            amount_retailprice
        FROM Books 
        ORDER BY amount_retailprice DESC LIMIT 5;
    """,
    "5.Find Books Published After 2010 with at Least 500 Pages": """
        SELECT 
            book_title,
            pagecount,
            year
        FROM Books 
        WHERE year > 2010 AND pagecount >= 500;
    """,
    "6.List Books with Discounts Greater than 20%": """
        SELECT 
            book_title, 
            amount_listPrice, 
            amount_retailPrice,
            ((amount_listPrice - amount_retailPrice) / amount_listPrice) * 100 AS discount_percentage
        FROM books
        WHERE ((amount_listPrice - amount_retailPrice) / amount_listPrice) * 100 > 20;
    """,
    "7.Find the Average Page Count for eBooks vs Physical Books": """
        SELECT 
            CASE
                WHEN isEbook = TRUE THEN 'eBook'
                ELSE 'Physical Book'
            END AS book_type,
            AVG(pagecount) AS avgepagecount
        FROM books 
        GROUP BY isEbook;
    """,
    "8.Find the Top 3 Authors with the Most Books": """
        SELECT author, COUNT(*) AS books_count
        FROM (
            SELECT TRIM(value) AS author
            FROM books
            CROSS JOIN JSON_TABLE(
                CONCAT('["', REPLACE(book_authors, ',', '","'), '"]'),
                '$[*]' COLUMNS (value VARCHAR(255) PATH '$')
            ) AS authors
            WHERE book_authors IS NOT NULL AND book_authors != ''
        ) AS author_list
        GROUP BY author
        ORDER BY books_count DESC LIMIT 3;
    """,
    "9.List Publishers with More than 10 Books": """
        SELECT
            publisher,
            COUNT(*) AS BooksCount
        FROM books 
        WHERE publisher != ''
        GROUP BY publisher
        HAVING BooksCount > 10;
    """,
    "10.Find the Average Page Count for Each Category": """
        SELECT 
            categories, 
            AVG(pagecount) 
        FROM Books 
        WHERE categories != ''
        GROUP BY categories;
    """,
    "11.Retrieve Books with More than 3 Authors": """
        SELECT 
            book_title, 
            book_authors 
        FROM books
        WHERE LENGTH(book_authors) - LENGTH(REPLACE(book_authors, ',', '')) + 1 > 3;
    """,
    "12.Books with Ratings Count Greater Than the Average": """
        SELECT 
            book_title, 
            ratingsCount 
        FROM books
        WHERE ratingsCount > (SELECT AVG(ratingsCount) FROM books);
    """,
    "13.Books with the Same Author Published in the Same Year": """
        SELECT 
            book_authors, 
            year, 
            GROUP_CONCAT(book_title SEPARATOR ', ') AS books
        FROM books
        WHERE book_authors != '' AND year != ''
        GROUP BY book_authors, year
        HAVING COUNT(*) > 1;
    """,
    "14.Books with a Specific Keyword in the Title": """
        SELECT 
            book_authors, 
            book_title 
        FROM books 
        WHERE book_title LIKE '%India%';
    """,
    "15.Year with the Highest Average Book Price": """
        SELECT 
            year, 
            AVG(amount_listPrice) AS avg_price
        FROM books 
        WHERE year != ''
        GROUP BY year
        ORDER BY avg_price DESC LIMIT 1;
    """,
    "16.Count Authors Who Published 3 Consecutive Years": """
        WITH AuthorYears AS (
            SELECT 
                TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(book_authors, ',', numbers.n), ',', -1)) AS author,
                CAST(year AS UNSIGNED) AS published_year
            FROM books
            CROSS JOIN (
                SELECT 1 AS n UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5
            ) numbers
            WHERE 
                numbers.n <= 1 + CHAR_LENGTH(book_authors) - CHAR_LENGTH(REPLACE(book_authors, ',', ''))
                AND book_authors != '' AND year != ''
            GROUP BY author, published_year
        ),
        ConsecutiveYears AS (
            SELECT 
                author,
                COUNT(*) AS consecutive_count
            FROM (
                SELECT 
                    author,
                    published_year,
                    published_year - ROW_NUMBER() OVER (PARTITION BY author ORDER BY published_year) AS year_group
                FROM AuthorYears
            ) grouped_years
            GROUP BY author, year_group
            HAVING consecutive_count >= 3
        )
        SELECT COUNT(DISTINCT author) AS authors_with_3_consecutive_years FROM ConsecutiveYears;
    """,
    "17.Authors with Books Published in the Same Year but Different Publishers": """
        WITH SplitAuthors AS (
            SELECT
                TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(book_authors, ',', numbers.n), ',', -1)) AS author,
                year,
                publisher,
                book_id
            FROM books
            CROSS JOIN (
                SELECT 1 AS n UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5
            ) numbers
            WHERE numbers.n <= 1 + CHAR_LENGTH(book_authors) - CHAR_LENGTH(REPLACE(book_authors, ',', ''))
              AND book_authors != ''
        ),
        AuthorPublications AS (
            SELECT
                author,
                year,
                COUNT(DISTINCT publisher) AS publisher_count,
                COUNT(DISTINCT book_id) AS book_count
            FROM SplitAuthors
            WHERE year != '' AND publisher != ''
            GROUP BY author, year
            HAVING publisher_count > 1
        )
        SELECT 
            author,
            year,
            book_count AS total_books
        FROM AuthorPublications ORDER BY author, year;
    """,
    "18.Find the Average Retail Price of eBooks and Physical Books": """
        SELECT 
            AVG(CASE WHEN isEbook = true THEN amount_retailPrice END) AS avg_ebook_price,
            AVG(CASE WHEN isEbook = false THEN amount_retailPrice END) AS avg_physical_price
        FROM Books;
    """,
    "19.Books with Ratings More Than Two Standard Deviations Away": """
        WITH Stats AS (
            SELECT 
                AVG(averageRating) AS avg_rating,
                stddev(averageRating) AS stddev_rating
            FROM Books
        )
        SELECT 
            B.book_title,
            B.averageRating,
            B.ratingsCount
        FROM Books B, Stats S
        WHERE ABS(B.averageRating - S.avg_rating) > 2 * S.stddev_rating;
    """,
    "20.Publisher with the Highest Average Rating (with More Than 10 Books)": """
        SELECT 
            publisher,
            AVG(averageRating) AS average_rating,
            COUNT(*) AS number_of_books
        FROM Books
        GROUP BY publisher
        HAVING COUNT(*) > 10
        ORDER BY average_rating DESC LIMIT 1;
    """
    }
    return faq_queries
def get_axis():
    x_axis = ["","book_type","publisher","publisher","book_title","book_title","book_title","book_type","author","publisher","categories",
          "book_title","book_title","book_authors","book_title","year","","author","","book_title","publisher"]
    return x_axis
