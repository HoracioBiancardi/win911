from pylogix import PLC  # Arquivos da conexão com o CLP
from datetime import datetime, timedelta

import time
import sys

import smtplib
from email.message import EmailMessage
import imghdr

import sqlite3

sys.path.append("..")


# ###########################################################################################
# ###          Criação das variáveis, definir os IPs do CLP.                              ###
# ###########################################################################################

# ip do CLP
ipCLP = "10.188.131.1"
ipCLP2 = "10.188.131.2"

# ###########################################################################################
# ###          Rotinas de varredura de dispositivos na rede, com comunicação CIP          ###
# ###########################################################################################
"""
Rotinas de varredura de dispositivos na rede, com comunicação CIP, sendo a máscara de
sub-rede definida para: 255.255.255.255

OBS: Para definir outra máscara, acesse o arquivo 'eip.py' linha 642 e linha 661 e altere
a máscara.
"""


def enviaEmail():
    EMAIL_ADDRESS = "sistemas_ta@ferroport.com.br"

    with open("toEmail.txt", "r") as f:
        toEmail = f.read()
        # print(toEmail)

    with open("controle_sensores.txt", "r") as f:
        contr_sensores = f.read()

    msg = EmailMessage()
    msg["Subject"] = "Monitoramento de Preditiva"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = toEmail

    # print(contr_sensores)

    msg.add_alternative(
        """
<!DOCTYPE html>
<html>
    <head>
	
    </head>
     <boby style="margin: 0; padding: 0;">
        <table  cellpadding"0" width="1000px" style="border-collapse: collapse;">
            <tr>
                <td align="center">
                <img src="logo.jpeg" style="max-width:100%; height:auto;">
                </td>
            </tr>
        </table>
        <table  border="1"  width="1500px" style="border-collapse: collapse;">
            <tr style="text-align: center; background-color: #cccccc;">
        
        <td><b>&nbsp;Data&nbsp;</b></td>
		<td><b>&nbsp;Tag&nbsp;</b></td>
        <td><b>&nbsp;Equipamento&nbsp;</b></td>
        <td><b>&nbsp;Tag Def_ALM&nbsp;</b></td>
		<td><b>&nbsp;Descrição&nbsp;</b></td>
		<td><b>&nbsp;Alarme(H)&nbsp;</b></td>
		<td><b>&nbsp;Alarme(HH)&nbsp;</b></td>
		<td><b>&nbsp;Valor Atual&nbsp;</b></td>
		<td><b>&nbsp;Alarme Ativo&nbsp;</b></td>
	    </tr>
	    <tr>

	    """
        + contr_sensores
        + """
	    </tr>
        </table>
    </body>
</html>
        """,
        subtype="html",
    )

    with open("logo.jpeg", "rb") as f:
        fileData = f.read()
        fileType = imghdr.what(f.name)
        fileName = f.name

    msg.add_attachment(fileData, maintype="image", subtype=fileType, filename=fileName)

    with smtplib.SMTP("10.27.1.9", 25) as smtp:
        smtp.send_message(msg)


def db_sensores_escrever(
    Data, Tag, CLP, Tag_Def_ALM, Descricao, AlarmeH, AlarmeHH, ValorAtual, ValorAtivo
):
    with sqlite3.connect("basededados.db") as conexao:
        cursor = conexao.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS sensores_preditiva ("
            "Data DATE,"
            "Tag TEXT,"
            "CLP TEXT,"
            "Tag_Def_ALM TEXT,"
            "Descricao TEXT,"
            "AlarmeH REAL,"
            "AlarmeHH REAL,"
            "ValorAtual REAL,"
            "ValorAtivo TEXT )"
        )

        cursor.execute(
            "INSERT INTO sensores_preditiva VALUES (:Data, :Tag, :CLP, :Tag_Def_ALM, :Descricao, :AlarmeH, :AlarmeHH, :ValorAtual, :ValorAtivo)",
            {
                "Data": Data,
                "Tag": Tag,
                "CLP": CLP,
                "Tag_Def_ALM": Tag_Def_ALM,
                "Descricao": Descricao,
                "AlarmeH": AlarmeH,
                "AlarmeHH": AlarmeHH,
                "ValorAtual": ValorAtual,
                "ValorAtivo": ValorAtivo,
            },
        )

        conexao.commit()


def db_sensores_ler(TAGS1):

    with open(f"{TAGS1}.txt", "r") as f:
        TAG1 = f.readlines()

    TAG_DEF1 = []
    TAG_ALM1 = []

    for x in TAG1:
        TAG_DEF1.append(x.replace("\n", "") + "_DEFEITO")

    for x in TAG1:
        TAG_ALM1.append(x.replace("\n", "") + "_ALARME")

    TAG_COM1 = TAG_ALM1 + TAG_DEF1

    for tag3 in TAG_COM1:
        print(tag3)
        with sqlite3.connect("basededados.db") as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                "SELECT * FROM sensores_preditiva WHERE Tag_Def_ALM LIKE '"
                + tag3.replace("\n", "")
                + "' ORDER BY Data ASC LIMIT 1"
            )

            for linha in cursor.fetchall():
                Data, Tag, CLP, Tag_Def_ALM, Descricao, AlarmeH, AlarmeHH, ValorAtual, ValorAtivo = (
                    linha
                )

                # print(linha)

                with open("controle_sensores.txt", "a") as f:
                    f.write(f"<tr>")
                    f.write(f"<td>&nbsp;{Data}&nbsp;</td>")
                    f.write(f"<td>&nbsp;{Tag}&nbsp;</td>")
                    f.write(f"<td>&nbsp;{CLP}&nbsp;</td>")
                    f.write(f"<td>&nbsp;{Tag_Def_ALM}&nbsp;</td>")
                    f.write(f"<td>&nbsp;{Descricao}&nbsp;</td>")
                    f.write(f"<td>&nbsp;{AlarmeH}&nbsp;</td>")
                    f.write(f"<td>&nbsp;{AlarmeHH}&nbsp;</td>")
                    f.write(f"<td>&nbsp;{ValorAtual}&nbsp;</td>")
                    f.write(f"<td>&nbsp;{ValorAtivo}&nbsp;</td>")
                    f.write(f"</tr>")


def db_apaga_banco():
    with sqlite3.connect("basededados.db") as conexao:
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM sensores_preditiva")
        conexao.commit()


def leitura_clp(IP_CLP, TAGS, clp_nome):

    encontrado = False
    with PLC() as comm:
        dispositivos = comm.Discover()
        for dispositivo in dispositivos.Value:
            clpEncontrado = dispositivo.IPAddress
            if clpEncontrado == IP_CLP:
                encontrado = True
                break

    try:
        if encontrado:
            with PLC() as comm:
                comm.IPAddress = IP_CLP

                with open(f"{TAGS}.txt", "r") as f:
                    TAG = f.readlines()

                TAG_DEF2 = []
                TAG_ALM2 = []

                for x in TAG:
                    TAG_DEF2.append((x.replace("\n", "") + "_DEFEITO", 193))

                for x in TAG:
                    TAG_ALM2.append((x.replace("\n", "") + "_ALARME", 193))

                TAG_COM2 = TAG_DEF2 + TAG_ALM2

                tags = comm.Read(TAG_COM2)

                # comm.Write("",)

                TAG_DEF = []
                TAG_ALM = []

                for x in TAG:
                    TAG_DEF.append(x.replace("\n", "") + "_DEFEITO")

                for x in TAG:
                    TAG_ALM.append(x.replace("\n", "") + "_ALARME")

                TAG_COM = TAG_DEF + TAG_ALM

                data_atual = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

                i = 0
                for tag in tags:
                    i = i + 1

                    if tag.Value == True:

                        tag_sensor = TAG_COM[i - 1][:10]

                        ret_tags = [
                            [tag_sensor + "_ALM.HHLimit", 196],
                            [tag_sensor + "_ALM.HLimit", 196],
                            [tag_sensor + ".VAL_PV_OUT", 196],
                            [tag_sensor + "_DSC.ANA", 160],
                        ]

                        ret = comm.Read(ret_tags)

                        limit_HH = round(ret[0].Value, 2)
                        limit_H = round(ret[1].Value, 2)
                        valor_atual = round(ret[2].Value, 2)
                        desc = str(ret[3].Value)

                        db_sensores_escrever(
                            data_atual,
                            tag_sensor,
                            clp_nome,
                            TAG_COM[i - 1],
                            desc,
                            limit_H,
                            limit_HH,
                            valor_atual,
                            "SIM",
                        )

    except Exception as e:
        print(f"falha de conexoa {e}")


while True:
    # IP_CLP, TAGS, clp_nome
    leitura_clp(ipCLP, "tag_ep01", "EP01")
    leitura_clp(ipCLP, "tag_ep02", "EP02")
    leitura_clp(ipCLP, "tag_20tr01", "3220-TR-01")
    leitura_clp(ipCLP, "tag_20tr02", "3220-TR-02")
    leitura_clp(ipCLP, "tag_20tr03", "3220-TR-03")
    leitura_clp(ipCLP2, "tag_rc", "RC01")
    leitura_clp(ipCLP2, "tag_cn", "CN01")

    horaAtual = str(datetime.now().strftime("%H:%M:%S"))

    # print(horaAtual)
    if (
        horaAtual == "23:50:01"
        or horaAtual == "23:50:02"
        or horaAtual == "23:50:03"
        or horaAtual == "23:50:04"
        or horaAtual == "23:50:05"
        or horaAtual == "23:50:06"
        or horaAtual == "23:50:07"
        or horaAtual == "23:50:08"
        or horaAtual == "23:50:09"
        or horaAtual == "23:50:10"
        or horaAtual == "23:50:11"
        or horaAtual == "23:50:12"
        or horaAtual == "23:50:13"
        or horaAtual == "23:50:14"
        or horaAtual == "23:50:15"
        #########################
        or horaAtual == "03:10:01"
        or horaAtual == "03:10:02"
        or horaAtual == "03:10:03"
        or horaAtual == "03:10:04"
        or horaAtual == "03:10:05"
        or horaAtual == "03:10:07"
        or horaAtual == "03:10:08"
        or horaAtual == "03:10:09"
        or horaAtual == "03:10:10"
        or horaAtual == "03:10:11"
        or horaAtual == "03:10:12"
        or horaAtual == "03:10:13"
        or horaAtual == "03:10:14"
        or horaAtual == "03:10:15"
        #########################
        or horaAtual == "06:10:01"
        or horaAtual == "06:10:02"
        or horaAtual == "06:10:03"
        or horaAtual == "06:10:04"
        or horaAtual == "06:10:05"
        or horaAtual == "06:10:06"
        or horaAtual == "06:10:07"
        or horaAtual == "06:10:08"
        or horaAtual == "06:10:09"
        or horaAtual == "06:10:10"
        or horaAtual == "06:10:11"
        or horaAtual == "06:10:12"
        or horaAtual == "06:10:13"
        or horaAtual == "06:10:14"
        or horaAtual == "06:10:15"
        #########################
        or horaAtual == "09:10:01"
        or horaAtual == "09:10:02"
        or horaAtual == "09:10:03"
        or horaAtual == "09:10:04"
        or horaAtual == "09:10:05"
        or horaAtual == "09:10:06"
        or horaAtual == "09:10:07"
        or horaAtual == "09:10:08"
        or horaAtual == "09:10:09"
        or horaAtual == "09:10:10"
        or horaAtual == "09:10:11"
        or horaAtual == "09:10:12"
        or horaAtual == "09:10:13"
        or horaAtual == "09:10:14"
        or horaAtual == "09:10:15"
        #########################
        or horaAtual == "09:30:01"
        or horaAtual == "09:30:02"
        or horaAtual == "09:30:03"
        or horaAtual == "09:30:04"
        or horaAtual == "09:30:05"
        or horaAtual == "09:30:06"
        or horaAtual == "09:30:07"
        or horaAtual == "09:30:08"
        or horaAtual == "09:30:09"
        or horaAtual == "09:30:10"
        or horaAtual == "09:30:11"
        or horaAtual == "09:30:12"
        or horaAtual == "09:30:13"
        or horaAtual == "09:30:14"
        or horaAtual == "09:30:15"
        #########################
        or horaAtual == "12:10:01"
        or horaAtual == "12:10:02"
        or horaAtual == "12:10:03"
        or horaAtual == "12:10:04"
        or horaAtual == "12:10:05"
        or horaAtual == "12:10:06"
        or horaAtual == "12:10:07"
        or horaAtual == "12:10:08"
        or horaAtual == "12:10:09"
        or horaAtual == "12:10:10"
        or horaAtual == "12:10:11"
        or horaAtual == "12:10:12"
        or horaAtual == "12:10:13"
        or horaAtual == "12:10:14"
        or horaAtual == "12:10:15"
        #########################
        or horaAtual == "15:10:01"
        or horaAtual == "15:10:02"
        or horaAtual == "15:10:03"
        or horaAtual == "15:10:04"
        or horaAtual == "15:10:05"
        or horaAtual == "15:10:06"
        or horaAtual == "15:10:07"
        or horaAtual == "15:10:08"
        or horaAtual == "15:10:09"
        or horaAtual == "15:10:10"
        or horaAtual == "15:10:11"
        or horaAtual == "15:10:12"
        or horaAtual == "15:10:13"
        or horaAtual == "15:10:14"
        or horaAtual == "15:10:15"
        #########################
        or horaAtual == "18:10:01"
        or horaAtual == "18:10:02"
        or horaAtual == "18:10:03"
        or horaAtual == "18:10:04"
        or horaAtual == "18:10:05"
        or horaAtual == "18:10:06"
        or horaAtual == "18:10:07"
        or horaAtual == "18:10:08"
        or horaAtual == "18:10:09"
        or horaAtual == "18:10:10"
        or horaAtual == "18:10:11"
        or horaAtual == "18:10:12"
        or horaAtual == "18:10:13"
        or horaAtual == "18:10:14"
        or horaAtual == "18:10:15"
        #########################
        or horaAtual == "21:10:01"
        or horaAtual == "21:10:02"
        or horaAtual == "21:10:03"
        or horaAtual == "21:10:04"
        or horaAtual == "21:10:05"
        or horaAtual == "21:10:06"
        or horaAtual == "21:10:07"
        or horaAtual == "21:10:08"
        or horaAtual == "21:10:09"
        or horaAtual == "21:10:10"
        or horaAtual == "21:10:11"
        or horaAtual == "21:10:12"
        or horaAtual == "21:10:13"
        or horaAtual == "21:10:14"
        or horaAtual == "21:10:15"
        #########################
        
    ):

        db_sensores_ler("tag_ep01")
        db_sensores_ler("tag_ep02")
        db_sensores_ler("tag_20tr01")
        db_sensores_ler("tag_20tr02")
        db_sensores_ler("tag_20tr03")
        db_sensores_ler("tag_cn")
        db_sensores_ler("tag_rc")

        with open("controle_sensores.txt", "r") as f:
            contr_sensor = f.read()

        if contr_sensor != " ":
            enviaEmail()
            db_apaga_banco()
            with open("controle_sensores.txt", "w") as f:
                f.write(" ")
            time.sleep(15)

