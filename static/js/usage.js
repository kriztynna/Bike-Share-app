// JavaScript for chart
google.load('visualization', '1.0', {'packages':['corechart']});
    
function handleData(){
    if (request.readyState == 4 && request.status == 200){
        var json_output = request.responseText;
        chartJSON = JSON.parse(json_output);

        var data = new google.visualization.DataTable();
        columns = chartJSON.dataTable.cols
        for (var i=0;i<columns.length;i++){
            data.addColumn(columns[i].type, columns[i].id);
        }

        rows = chartJSON.dataTable.rows
        rowsToAdd = new Array();
        for (var i=0;i<rows.length;i++){
            var row = new Array();
            for (var j=0;j<rows[i].c.length;j++){
                if (j==0) {
                    var value = new Date(rows[i].c[j].v);
                }
                else {
                    var value = rows[i].c[j].v;
                }
                row.push(value);
            }
            rowsToAdd.push(row);
        }
        data.addRows(rowsToAdd);

        var options = chartJSON.options;

        var chart = new google.visualization.LineChart(document.getElementById('chart_div'));
        chart.draw(data, options);
    }
}

function drawChart(){
    request = new XMLHttpRequest();
    request.onreadystatechange = handleData;
    var req = 'usagejson?view=trips';
    var encoded_req = encodeURI(req);
    request.open("GET",encoded_req,true);
    request.send();
}
document.body.onload=drawChart;

function updateChart(){
    var chart_div = document.getElementById('chart_div');
    chart_div.innerHTML='<h3 class="load_text" id="load_text1"><br><br><br>adjusting seat...</h3><h3 class="load_text" id="load_text2"><br><br><br><br>... putting on helmet</h3><h3 class="load_text" id="load_text3"><br><br><br><br><br>... and off we go!</h3>'

    var datasets_dropdown = document.getElementById('datasets_dropdown');
    var view = datasets_dropdown.options[datasets_dropdown.selectedIndex].value;

    request = new XMLHttpRequest();
    request.onreadystatechange = handleData;

    var req = 'usagejson?view='+view;
    var encoded_req = encodeURI(req);
    request.open("GET",encoded_req,true);
    request.send();
}
