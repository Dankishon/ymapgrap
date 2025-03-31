from main import CoordinateGrabber

def main():
    org_type = "Стоматология"

    # 🧪 Мини-сетка для быстрого теста (3 точки)
    lat_range = [55.75]
    lon_range = [37.61]

    # 👇 Ограничиваем до 2 карточек на ячейку
    grabber = CoordinateGrabber(
        org_type=org_type,
        lat_range=lat_range,
        lon_range=lon_range,
        step=0.02,
        per_cell_limit=2
    )

    grabber.grab_data()

if __name__ == '__main__':
    main()
