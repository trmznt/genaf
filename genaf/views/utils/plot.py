
# general plot / graphics utility using matplotlib

from genaf.views.tools import *

from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

import pandas
import io, base64


@roles( PUBLIC )
def index(request):

    # check

    if not request.GET.get('_method', None) in [ '_exec', '_dfexec' ]:

        pform, jscode = create_form( request )

        return render_to_response('genaf:templates/utils/index.mako',
            {   'title': 'Plotting Utility',
                'html': pform,
                'code': jscode,
            }, request = request )

    if request.GET.get('method') == '_dfexec':
        df = parse_df(request.GET.get('dfdata'))
    else:
        df = parse_textdata(request.GET.get('textdata'))
    plot_type = request.GET.get('plot_type')

    if plot_type == 'B':
        html, jscode = column_chart(df)
    elif plot_type == 'S':
        return error_page(request, 'Scatter plot not implemented yet')
    elif plot_type == 'P':
        html, jscode = pie_chart(df)

    return render_to_response('genaf:templates/utils/index.mako',
            {   'title': 'Plot',
                'html': html,
                'code': jscode,
            }, request = request )



def create_form(request):
    """ return html, jscode """

    pform = form(name='plotform', action='#')

    pform.add(
        fieldset(name='data')[
            input_textarea('textdata', label='Data'),
        ],
        fieldset(name='options')[
            input_select(name='plot_type', label='Plot type', value='B',
                    options = [ ('B', 'Bar (vertical) / column chart'),
                                ('S', 'Scatter x,y plot'),
                                ('P', 'Pie chart'),
                    ] ),
        ],
        fieldset()[ submit_bar('Create plot', '_exec')]
    )
    return (pform, '')


def parse_textdata(textdata):
    """ parse data, with the first line as header, and consecutive lines as data """
    header, content = textdata.split('\n', 1)
    columns = [ x.strip() for x in header.split('|') ]
    buff = io.StringIO(content)

    dataframe = pandas.read_table(buff, header=None, names = columns)

    return dataframe


def save_figure(canvas):

    figfile = io.BytesIO()
    canvas.print_figure(figfile)
    figfile.seek(0)
    figdata_png = figfile.getvalue()

    figdata_png = base64.b64encode(figdata_png).decode('ASCII')

    fig_html = literal('<img src="data:image/png;base64,%s" >' % figdata_png)

    return fig_html,''


def column_chart(df):
    """ creates column (vertical bar) chart """

    fig = Figure()
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)

    ax.bar(df.index, df.iloc[:,1], align='center')
    ax.set_xlabel(df.columns[0])
    ax.set_xticks(df.index)
    ax.set_xticklabels(df.iloc[:,0], rotation='vertical')
    ax.set_ylabel(df.columns[1])
    fig.tight_layout()

    return save_figure(canvas)


def pie_chart(df):

    fig = Figure()
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111, aspect=1)

    ax.pie( df.iloc[:,1], labels = df.iloc[:,0], counterclock=False, startangle=90 )
    ax.set_xlabel(df.columns[0])
    fig.tight_layout()

    return save_figure(canvas)
