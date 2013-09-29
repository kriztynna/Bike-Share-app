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

        var chart = new google.visualization.AreaChart(document.getElementById('chart_div'));
        chart.draw(data, options);
    }
}

function drawChart(){
    request = new XMLHttpRequest();
    request.onreadystatechange = handleData;
    var req = 'totalsjson?time_req=86400&bikes_req=checked';
    var encoded_req = encodeURI(req);
    request.open("GET",encoded_req,true);
    request.send();
}

document.body.onload=drawChart;

function updateChart(){
    var chart_div = document.getElementById('chart_div');
    chart_div.innerHTML='<h3 class="load_text" id="load_text1"><br><br><br>adjusting seat...</h3><h3 class="load_text" id="load_text2"><br><br><br><br>... putting on helmet</h3><h3 class="load_text" id="load_text3"><br><br><br><br><br>... and off we go!</h3>'

    var time_dropdown = document.getElementById('time_dropdown');
    var time_req = time_dropdown.options[time_dropdown.selectedIndex].value;                
    var bikes_checkbox = document.getElementById('bikes_checkbox');
    var bikes_req
    if (bikes_checkbox.checked==true){
        bikes_req = 'checked';
    }
    else {
        bikes_req=''
    }
    
    var docks_checkbox = document.getElementById('docks_checkbox');
    var docks_req
    if (docks_checkbox.checked==true){
        docks_req = 'checked';
    }
    else {
        docks_req=''
    }

    request = new XMLHttpRequest();
    request.onreadystatechange = handleData;

    var req = 'totalsjson?'+'time_req='+time_req+'&bikes_req='+bikes_req+'&docks_req='+docks_req;
    var encoded_req = encodeURI(req);
    request.open("GET",encoded_req,true);
    request.send();
}