# football
Python Dash Oracle Ploty Adaptation from Tutorial written by "Aly Sivji"

Please refer to Aly Sivji posting for a nice description of this portal https://alysivji.github.io/reactive-dashboards-with-dash.html

This was a learning exercise not intended to
   - handle large amounts of data
   - explore best practices in data model
   - use best practices on advanced Python ... I am not a python developer.
   
Major modifications were:
   - Original design reads same dataframe to use in 3 callbacks. Now it reads only one time
   - Logic was added to avoid triggering callbacks if any of the dropdowns still not populated
   - Added a Submit bottom
   - A column date was renamed to dateg as in Oracle is it a reserved word
   
All flaws you encountered please feedback so I can improve my 0.1% knowledge on this subject.

Thanks.
Borba.
