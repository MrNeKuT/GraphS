from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def plot_graph():
    return render_template('nx.html')


@app.route('/random-routes')
def plot_rr_graph():
    return render_template('nx_rr.html')


@app.route('/random-routes/my')
def plot_rr_graph_my():
    return render_template('nx_rr_my.html')


if __name__ == '__main__':
    app.run(debug=True)
