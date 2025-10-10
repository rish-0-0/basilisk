*** Important to write extremely well documented code, with proper readable directory structure, and even backtrack to change said structure so that it can better adapt to code maintanability. Code Maintainability cannot be sacrificed for more features. Use the dependency injection pattern as much as needed. ***


1. We need to build for graphql and also rest api alike.
2. For REST APIs we should be able to parse GET query params to meaningful SQL like queries which SQLAlchemy can use. You can use any technique. You could use a famous package for query parsing in python if it exists, but it should be pretty standard. I prefer the GitHub syntax, like ?assignee=A,B,C&author=A,B,C etc something like that. It should support passing in SQL like keywords while still not letting an injection happen. 
Stuff like groupBy=col1,col2,col3 or orderBy=[(col1, Asc), (col2, Desc)]
and also select statements which allows to select a part of the table: select=col1,col2,col3, 

not only that, some useful functions which can be embedded in the select statement: select=col1,col2,sum(col3)&groupBy=col3

and also the rename

?select=sum(col1);sum_col_1,col2,count(col3);count&groupBy=col1,col3

*** Important: I have given some examples of REST based queries, but it's your choice to follow this syntax. You can use your own, or an industry standard ***

3. For graphql, basic support integration is enough, but we should support all the popular operators like limit, offset, where, group, order, select. also write mutations.

4. For pagination in REST mode just use limit, offset for now. We are writing crud routes, not actual production code. 

5. Use ariadne python package for graphql support. take in input from pydantic models for either graphql, rest

6. Use SQLite for testing. You should support a /documentation path which gives the Swagger docs for all the CRUD routes for that model. You can use a package for that if necessary.

7. Leave authentication out for now. We will add support for that later.

8. Idea is simple: pass in a pydantic model -> get a fully functional CRUD routes from it.

9. Keep well named files, so we can import not only just schema generator or router generator. We can import, say query parser, or just the authentication dependency (future).

10. The idea is to keep everything very modular, while providing as much value as possible to the developer using fastapi for graphql, etc. And a database. For scaffolding apps, this should be a perfect go to package.

