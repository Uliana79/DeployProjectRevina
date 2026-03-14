from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel, Field
from pydantic import field_validator
import re
import pandas as pd
from datetime import datetime
from typing import List

app = FastAPI()

class ElectricityCreate(BaseModel):
    timestep: str
    consumption_eur: float = Field(ge=0, description="consumption_eur не может быть меньше 0")
    consumption_sib: float = Field(ge=0, description="consumption_sib не может быть меньше 0")
    price_eur: float = Field(ge=0, description="price_eur не может быть меньше 0")
    price_sib: float = Field(ge=0, description="price_sib не может быть меньше 0")

    @field_validator('timestep')
    @classmethod
    def validate_timestep(cls, v:str) -> str:
        if not re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$', v):
            raise ValueError('timestep должен быть в формате "YYYY-MM-DD HH:MM"')
        
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError('Некорректная дата или время')
        
        return v 
    
    @field_validator('price_eur', 'price_sib')
    @classmethod
    def round_price(cls, v: float) -> float:
        return round(v, 2)    

class Electricity(ElectricityCreate):
    id: int


class PageRecords(BaseModel):
    total: int
    page: int
    total_pages: int
    records: List[Electricity]


def get_total_records() -> int:
    try:
        with open("RU_Electricity_Market_PZ_dayahead_price_volume.csv", 'r') as f:
            count = 0
            for _ in f:
                count += 1
            return  count-1
    except:
        return 0


def read_csv() -> pd.DataFrame:
    try:        
        df = pd.read_csv("RU_Electricity_Market_PZ_dayahead_price_volume.csv") 
        if not df.empty:
            df.insert(0, 'id', range(1, len(df) + 1))
        return df
    except Exception as e:
        print(f"Ошибка: {e}")
        return pd.DataFrame(columns=['id', 'timestep', 'consumption_eur', 
                                    'consumption_sib', 'price_eur', 'price_sib'])


def read_csv_page(skip: int) -> pd.DataFrame:
    try:
        df = pd.read_csv(
            "RU_Electricity_Market_PZ_dayahead_price_volume.csv",
            skiprows=range(1, skip+1) if skip>0 else None,
            nrows=1000
        )
        if not df.empty:
            df.insert(0, 'id', range(skip+1, skip+len(df)+1))
        return df
    except:
        return pd.DataFrame(columns=['id', 'timestep', 'consumption_eur', 
                                    'consumption_sib', 'price_eur', 'price_sib'])


def write_csv(df:pd.DataFrame) -> None:
    try:
        if 'id' in df.columns:
            df = df.drop('id', axis=1)
        df.to_csv("RU_Electricity_Market_PZ_dayahead_price_volume.csv", index=False)
    except Exception as e:
        print(f"Ошибка: {e}")
        raise


@app.get("/records", response_model=PageRecords, status_code=status.HTTP_201_CREATED)
async def read_records(page: int = Query(1, ge=1, description="Номер страницы")) -> PageRecords:
    try:
        total = get_total_records()
        if total == 0:
            return PageRecords(
                total=0,
                page=page,
                total_pages=0,
                records=[]
            )
        
        total_pages = (total + 1000 - 1)//1000
        if page > total_pages:
            page = total_pages
        skip = (page - 1) * 1000
        page_df = read_csv_page(skip)
        
        records: list[Electricity] = []
        for record in page_df.to_dict('records'):
            record_str = {str(k): v for k, v in record.items()}
            records.append(Electricity(**record_str))
        
        return PageRecords(
            total=total,
            page=page,
            total_pages=total_pages,
            records=records
        )
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка: {e}")


@app.post("/records", response_model=Electricity, status_code=status.HTTP_201_CREATED)
async def create_record(data: ElectricityCreate) -> Electricity:
    try:
        df = read_csv()
        if df.empty:
            new_id = 1
        else:
            new_id = df['id'].max() + 1

        new_record = Electricity(
            id=new_id,
            timestep=data.timestep,
            consumption_eur=data.consumption_eur,
            consumption_sib=data.consumption_sib,
            price_eur=data.price_eur,
            price_sib=data.price_sib
        )
        
        new_df = pd.DataFrame([new_record.model_dump()])
        df = pd.concat([df, new_df], ignore_index=True)
        write_csv(df)
        return new_record    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка создания записи: {e}")


@app.delete("/records/{id}", status_code=status.HTTP_200_OK)
async def delete_record(id: int) -> dict[str,str]:
    try:
        df = read_csv()
        if id not in df['id'].values:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ID={id} не найден")

        df = df[df['id'] != id]
               
        write_csv(df)
        return {"detail": f"Запись с ID={id} удалена"}    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка удаления записи: {e}")
    
    
@app.get("/records/all", response_model=List[Electricity])
async def get_all_records() -> list[Electricity]:
    try:
        df = read_csv()
        if df.empty:
            return []
        
        records: list[Electricity] = []
        for record in df.to_dict('records'):
            record_str = {str(k): v for k, v in record.items()}
            records.append(Electricity(**record_str))
        
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {e}")