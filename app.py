from flask import Flask, render_template

app = Flask(
    __name__,
    template_folder="modules/nav/templates",
    static_folder="modules/nav/static"
)

@app.route("/")
def nav():
    return render_template("nav.html")

if __name__ == "__main__":
    app.run(debug=True)