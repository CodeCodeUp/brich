import akshare as ak
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route('/stock_hold_management', methods=['GET'])
def get_stock_hold_management():
    code = request.args.get('code')
    name = request.args.get('name')

    if not code or not name:
        return jsonify({'error': 'Missing required parameters: code and name'}), 400

    try:
        data = ak.stock_hold_management_person_em(code, name)
        return jsonify(data.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/stock_hist_day', methods=['GET'])
def get_stock_hist_min():
    code = request.args.get('code')
    begin = request.args.get('begin')
    period = request.args.get('period', 'daily')

    if not code or not begin:
        return jsonify({'error': 'Missing required parameters: code and begin'}), 400

    try:
        quote = ak.stock_zh_a_hist(symbol=code, period=period, start_date=begin)
        return jsonify(quote.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
