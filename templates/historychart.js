    function drawChart() {
        var data = new google.visualization.DataTable();
            data.addColumn('datetime', 'Time');
            {% set single=0 %}
            {% if bikes_req == "checked" %}
                data.addColumn('number', 'Available bikes');
                {% set single = single + 1 %}
            {% endif %}
            {% if docks_req == "checked" %}
                data.addColumn('number', 'Available docks');
                {% set single = single + 1 %}
            {% endif %}
            {% if errors_req == "checked" %}
                data.addColumn('number', 'Station errors');
                {% set single = single + 1 %}
            {% endif %}
            {% if single > 1 %}
                {% for d in data_set %}
                    data.addRows([[ {{d[0]}}, {{d[1]}}, {{d[2]}}, {{d[3]}} ]]);
                {% endfor %}
            {% elif single == 1 %}
                {% for d in data_set %}
                    data.addRows([[ {{d[0]}}, {{d[1]}} ]]);
                {% endfor %}
            {% endif %}

        var options = {
            title:'    {{name|safe}}',
            colors: {{color|safe}},
            backgroundColor:{stroke:"#FFFFFF"},
            height:500,
            chartArea:{left:35,top:50,width:"80%",height:"80%"},
            fontSize:14,
            fontName:"Arial",
            hAxis:{baselineColor:"#FFFFFF",gridlines:{color:"#FFFFFF"}},
            vAxis:{baselineColor:"#556270",gridlines:{color:"#556270"},format:'#'},
            lineWidth:3,
            legend: {position: 'top'},
            isStacked:true,
            };
        // color palette: "cheer up emo kid" by electrikmonk at ColourLovers
        // available at http://www.colourlovers.com/palette/1930/cheer_up_emo_kid
        
        var chart = new google.visualization.AreaChart(document.getElementById('chart_div'));
        chart.draw(data, options);
    }
    drawChart();