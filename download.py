from pathlib import Path
import pandas as pd
from traceback import format_exc

symbols = ["MMM","ABT","ABBV","ABMD","ACN","ATVI","ADBE","AMD","AAP","AES","AFL","A","APD","AKAM","ALK","ALB","ARE","ALXN","ALGN","ALLE","LNT","ALL","GOOGL","GOOG","MO","AMZN","AMCR","AEE","AAL","AEP","AXP","AIG","AMT","AWK","AMP","ABC","AME","AMGN","APH","ADI","ANSS","ANTM","AON","AOS","APA","AIV","AAPL","AMAT","APTV","ADM","ANET","AJG","AIZ","T","ATO","ADSK","ADP","AZO","AVB","AVY","BKR","BLL","BAC","BK","BAX","BDX","BRK","BBY","BIO","BIIB","BLK","BA","BKNG","BWA","BXP","BSX","BMY","AVGO","BR","BF","CHRW","COG","CDNS","CPB","COF","CAH","KMX","CCL","CARR","CTLT","CAT","CBOE","CBRE","CDW","CE","CNC","CNP","CERN","CF","SCHW","CHTR","CVX","CMG","CB","CHD","CI","CINF","CTAS","CSCO","C","CFG","CTXS","CLX","CME","CMS","KO","CTSH","CL","CMCSA","CMA","CAG","CXO","COP","ED","STZ","COO","CPRT","GLW","CTVA","COST","CCI","CSX","CMI","CVS","DHI","DHR","DRI","DVA","DE","DAL","XRAY","DVN","DXCM","FANG","DLR","DFS","DISCA","DISCK","DISH","DG","DLTR","D","DPZ","DOV","DOW","DTE","DUK","DRE","DD","DXC","EMN","ETN","EBAY","ECL","EIX","EW","EA","EMR","ETR","EOG","EFX","EQIX","EQR","ESS","EL","ETSY","EVRG","ES","RE","EXC","EXPE","EXPD","EXR","XOM","FFIV","FB","FAST","FRT","FDX","FIS","FITB","FE","FRC","FISV","FLT","FLIR","FLS","FMC","F","FTNT","FTV","FBHS","FOXA","FOX","BEN","FCX","GPS","GRMN","IT","GD","GE","GIS","GM","GPC","GILD","GL","GPN","GS","GWW","HAL","HBI","HIG","HAS","HCA","PEAK","HSIC","HSY","HES","HPE","HLT","HFC","HOLX","HD","HON","HRL","HST","HWM","HPQ","HUM","HBAN","HII","IEX","IDXX","INFO","ITW","ILMN","INCY","IR","INTC","ICE","IBM","IP","IPG","IFF","INTU","ISRG","IVZ","IPGP","IQV","IRM","JKHY","J","JBHT","SJM","JNJ","JCI","JPM","JNPR","KSU","K","KEY","KEYS","KMB","KIM","KMI","KLAC","KHC","KR","LB","LHX","LH","LRCX","LW","LVS","LEG","LDOS","LEN","LLY","LNC","LIN","LYV","LKQ","LMT","L","LOW","LUMN","LYB","MTB","MRO","MPC","MKTX","MAR","MMC","MLM","MAS","MA","MKC","MXIM","MCD","MCK","MDT","MRK","MET","MTD","MGM","MCHP","MU","MSFT","MAA","MHK","TAP","MDLZ","MNST","MCO","MS","MOS","MSI","MSCI","NDAQ","NOV","NTAP","NFLX","NWL","NEM","NWSA","NWS","NEE","NLSN","NKE","NI","NSC","NTRS","NOC","NLOK","NCLH","NRG","NUE","NVDA","NVR","ORLY","OXY","ODFL","OMC","OKE","ORCL","OTIS","PCAR","PKG","PH","PAYX","PAYC","PYPL","PNR","PBCT","PEP","PKI","PRGO","PFE","PM","PSX","PNW","PXD","PNC","POOL","PPG","PPL","PFG","PG","PGR","PLD","PRU","PEG","PSA","PHM","PVH","QRVO","PWR","QCOM","DGX","RL","RJF","RTX","O","REG","REGN","RF","RSG","RMD","RHI","ROK","ROL","ROP","ROST","RCL","SPGI","CRM","SBAC","SLB","STX","SEE","SRE","NOW","SHW","SPG","SWKS","SLG","SNA","SO","LUV","SWK","SBUX","STT","STE","SYK","SIVB","SYF","SNPS","SYY","TMUS","TROW","TTWO","TPR","TGT","TEL","FTI","TDY","TFX","TER","TXN","TXT","TMO","TIF","TJX","TSCO","TT","TDG","TRV","TFC","TWTR","TYL","TSN","UDR","ULTA","USB","UAA","UA","UNP","UAL","UNH","UPS","URI","UHS","UNM","VLO","VAR","VTR","VRSN","VRSK","VZ","VRTX","VFC","VIAC","VTRS","V","VNT","VNO","VMC","WRB","WAB","WMT","WBA","DIS","WM","WAT","WEC","WFC","WELL","WST","WDC","WU","WRK","WY","WHR","WMB","WLTW","WYNN","XEL","XRX","XLNX","XYL","YUM","ZBRA","ZBH","ZION","ZTS"]
savepath = "data/market"

if __name__ == '__main__':
	Path(savepath).mkdir(exist_ok=True,parents=True)

	def generate_url(symbol):
		return ("https://query1.finance.yahoo.com/v7/finance/download/"
		+ symbol
		+ "?period1=1262304000&period2=1606780800&interval=1d&events=history&includeAdjustedClose=true")

	for symbol in symbols:
		print(symbol)
		try:
			pd.read_csv(generate_url(symbol)).to_csv(f"{savepath}/{symbol}.csv")
		except Exception:
			print(format_exc())