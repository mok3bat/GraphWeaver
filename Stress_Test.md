
## 🟢 Level 1 – Simple (single entity, direct fields)

1. *List all workbooks by name and ID.*
2. *Get the project name for the workbook “Regional Sales”.*
3. *Show all dashboards’ names and IDs.*
4. *Return the names of all Tableau users.*

---

## 🟡 Level 2 – Filtering & Nested Fields

5. *Get all workbooks owned by user “Jane Doe”.*
6. *Fetch all datasources where the name contains “Sales”.*
7. *List dashboards inside the workbook “Financial Overview”.*
8. *Find all tags attached to the workbook “Regional Sales”.*

---

## 🟠 Level 3 – Connections & Pagination

9. *Get the first 10 workbooks, sorted by name.*
10. *Paginate through datasources, retrieving 5 at a time, with IDs and names.*
11. *Fetch dashboards connection for workbook “Customer Insights” and return their IDs and names.*
12. *Get all fields from datasource “Orders” including their IDs and names, limited to 20 per page.*

---

## 🔴 Level 4 – Lineage / Multi-hop Queries

13. *For workbook “Regional Sales”, list embedded datasources and their upstream tables.*
14. *Get the lineage of the datasource “Orders” → show upstream tables and columns.*
15. *Show all views connected to the datasource “Inventory”.*
16. *Return the columns (IDs, names) of tables used by datasource “Marketing Analytics”.*

---

## ⚫ Level 5 – Complex Business-style Queries

17. *Find all dashboards inside workbooks owned by user “John Smith”.*
18. *Return the list of published datasources that are tagged as “Certified”.*
19. *Get all calculated fields from the datasource “Orders” with their formulas.*
20. *List all flows and their output steps.*
21. *Fetch workbooks that use a datasource connected to schema “finance”.*