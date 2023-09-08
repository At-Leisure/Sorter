//#include <iostream>
#include <cmath>

//����.so�ļ� ��gcc Դ�ļ�.cpp -shared -fPIC -o Ŀ���ļ�.so��
//ע�⣬Ҫ��.so�ļ�����device�ļ�����


// �����ٶȲ����������������붨ʱ��Ƶ�ʣ������ٶȴ�100��15100�Ķ�ʱ����Ƶϵ��������ʱ��

#define StartSpeed 100
#define EndSpeed 15100
#define SpeedStep 50
#define EachSpeedStep 14
#define TIMERINPUTCLOCK 84000000
#define TimerFrequency 6000000
#define SpeedChangeSegments (EndSpeed - StartSpeed) / SpeedStep

#define COS45D 0.7071

typedef unsigned short uint16_t;
typedef short int16_t;
typedef int int32_t;

uint16_t Speed[1000];
uint16_t ARRTable[1000];
float SumTimeTable[1000];
bool inited = 0;

void CoreXYTimeCalInit();

extern "C"
{
float TimeCalculate(int16_t deltaX, int16_t deltaY, int16_t SetSpeed);
}

// int main()
// {
// 	CoreXYTimeCalInit();
// 	cout << TimeCalculate(5000, 5000, 10000) << endl;
// }

void CoreXYTimeCalInit()
{
	Speed[0] = StartSpeed;
	for (uint16_t i = 1; i < SpeedChangeSegments; i++)
	{
		Speed[i] += Speed[i - 1] + SpeedStep;
	}

	for (uint16_t i = 0; i < SpeedChangeSegments; i++)
	{
		ARRTable[i] = TimerFrequency / Speed[i] - 1;
		if (i == 0)
		{
			SumTimeTable[i] = EachSpeedStep / (float)Speed[i];
		}
		else
		{
			SumTimeTable[i] = EachSpeedStep / (float)Speed[i] + SumTimeTable[i - 1];
		}
		// cout << "��" << i << "�� SPEED:" << Speed[i]
		//	<< " SumTime : " << SumTimeTable[i] << endl;
	}
}

extern "C"
{
	float TimeCalculate(int16_t deltaX, int16_t deltaY, int16_t SetSpeed)
	{
		if (!inited){
			inited = 1;
			CoreXYTimeCalInit();
		}
		if (deltaX == 0 && deltaY == 0)
		{
			return 0.0f;
		}

		int32_t square_deltaX = deltaX * deltaX;
		int32_t square_deltaY = deltaY * deltaY;
		int32_t square_Distance = square_deltaX + square_deltaY;
		float_t Distance = sqrt(square_Distance);

		int16_t Move1 = deltaX - deltaY;
		int16_t Move2 = -deltaX - deltaY;

		// ������1/2ת��ʹб��ʵ���ƶ��ľ���
		float_t Far1 = COS45D * Move1; // ������Ϊx,-y�н�
		float_t Far2 = COS45D * Move2; // ������Ϊx,y�н�

		// ������������б����ٶ�
		float_t Speed1 = fabsf(SetSpeed * Far1 / Distance); // ������Ϊx,-y�н�
		float_t Speed2 = fabsf(SetSpeed * Far2 / Distance); // ������Ϊx,y�н�

		// ������ٶ���
		uint16_t SpeedUPSegement1 = (ceil(Speed1) - StartSpeed) / SpeedStep;
		uint16_t SpeedUPSegement2 = (ceil(Speed2) - StartSpeed) / SpeedStep;

		// ����Ӽ��ٵ��˶�����
		int16_t SpeedChangeDistance1 = (Move1 == 0) ? 0 : SpeedUPSegement1 * EachSpeedStep * (Move1 / abs(Move1));
		int16_t SpeedChangeDistance2 = (Move2 == 0) ? 0 : SpeedUPSegement2 * EachSpeedStep * (Move2 / abs(Move2));

		// ���ټ���������
		int32_t SpeedUp1, SpeedDown1, SpeedUp2, SpeedDown2;
		// ���ٲ��ұ������
		int32_t SpeedChangeIndex1, SpeedChangeIndex2;
		// ����������
		int32_t Uniform1, Uniform2;

		if (abs(SpeedChangeDistance1) * 2 >= abs(Move1)) // M1�޷�������ָ���ٶ�
		{
			SpeedUp1 = (Move1 / 2) / EachSpeedStep * EachSpeedStep;
			SpeedDown1 = SpeedUp1;
			Uniform1 = Move1 - SpeedUp1 - SpeedDown1;
			SpeedChangeIndex1 = labs((SpeedUp1) / EachSpeedStep);
		}
		else
		{
			SpeedUp1 = SpeedChangeDistance1 / EachSpeedStep * EachSpeedStep;
			SpeedDown1 = SpeedUp1;
			Uniform1 = Move1 - SpeedUp1 - SpeedDown1;
			SpeedChangeIndex1 = labs((SpeedUp1) / EachSpeedStep);
		}
		if (abs(SpeedChangeDistance2) * 2 >= abs(Move2)) // M2�޷�������ָ���ٶ�
		{
			SpeedUp2 = (Move2 / 2) / EachSpeedStep * EachSpeedStep;
			SpeedDown2 = SpeedUp2;
			Uniform2 = Move2 - SpeedUp2 - SpeedDown2;
			SpeedChangeIndex2 = labs((SpeedUp2) / EachSpeedStep);
		}
		else
		{
			SpeedUp2 = SpeedChangeDistance2 / EachSpeedStep * EachSpeedStep;
			SpeedDown2 = SpeedUp2;
			Uniform2 = Move2 - SpeedUp2 - SpeedDown2;
			SpeedChangeIndex2 = labs((SpeedUp2) / EachSpeedStep);
		}
		float_t Runtime1, Runtime2, Runtime;
		Runtime1 = SumTimeTable[SpeedChangeIndex1] * 2 + fabs((float_t)Uniform1 / Speed[SpeedChangeIndex1]);
		Runtime2 = SumTimeTable[SpeedChangeIndex2] * 2 + fabs((float_t)Uniform2 / Speed[SpeedChangeIndex2]);
		Runtime = (Runtime1 > Runtime2) ? Runtime1 : Runtime2;

		return Runtime;
	}
}