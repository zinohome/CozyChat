/**
 * 前端内置工具实现
 * 
 * 这些工具可以在前端直接执行，无需调用后端 API，减少延迟。
 */

import { logger } from '@/utils/logger';

const log = logger.withTag('BuiltinTools');

/**
 * 计算器工具
 */
export class CalculatorTool {
  private readonly safeFunctions: Record<string, any> = {
    abs: Math.abs,
    round: Math.round,
    min: Math.min,
    max: Math.max,
    pow: Math.pow,
    sqrt: Math.sqrt,
    sin: Math.sin,
    cos: Math.cos,
    tan: Math.tan,
    asin: Math.asin,
    acos: Math.acos,
    atan: Math.atan,
    log: Math.log,
    log10: (x: number) => Math.log10(x),
    exp: Math.exp,
    floor: Math.floor,
    ceil: Math.ceil,
    PI: Math.PI,
    E: Math.E,
  };

  async execute(expression: string): Promise<string> {
    try {
      // 将 ^ 转换为 ** (幂运算)
      expression = expression.replace(/\^/g, '**');

      // 验证表达式安全性
      if (!this.isSafeExpression(expression)) {
        return '错误：表达式包含不安全的字符或操作';
      }

      // 构建安全的执行环境
      const safeDict: Record<string, any> = {
        ...this.safeFunctions,
      };

      // 使用 Function 构造函数安全执行（比 eval 更安全）
      // 注意：虽然 Function 构造函数比 eval 更安全，但仍然需要谨慎使用
      try {
        const func = new Function(
          ...Object.keys(safeDict),
          `"use strict"; return ${expression}`
        );

        const result = func(...Object.values(safeDict));

        // 检查结果是否为有效数字
        if (typeof result !== 'number' || !Number.isFinite(result)) {
          return '错误：计算结果无效';
        }

        // 检查除零错误
        if (!Number.isFinite(result)) {
          return '错误：除以零或计算结果无效';
        }

        // 格式化结果
        if (Number.isInteger(result)) {
          return String(result);
        } else {
          // 保留合理的小数位数
          const rounded = Math.round(result * 10000000000) / 10000000000;
          // 去除末尾的零
          return String(rounded).replace(/\.?0+$/, '');
        }
      } catch (evalError: any) {
        if (evalError.message?.includes('division by zero') || 
            evalError.message?.includes('除以零') ||
            !Number.isFinite(evalError)) {
          return '错误：除以零';
        }
        throw evalError;
      }
    } catch (error: any) {
      log.error('Calculator error:', error);
      return `错误：计算失败 - ${error.message || 'Unknown error'}`;
    }
  }

  private isSafeExpression(expression: string): boolean {
    // 禁止的危险字符和关键字
    const dangerous = [
      'import',
      'exec',
      'eval',
      '__',
      'open',
      'file',
      'input',
      'compile',
      'exit',
      'quit',
      'help',
      'vars',
      'dir',
      'globals',
      'locals',
      'window',
      'document',
      'process',
      'require',
      'module',
      'exports',
    ];

    const expressionLower = expression.toLowerCase();
    for (const item of dangerous) {
      if (expressionLower.includes(item)) {
        return false;
      }
    }

    // 只允许字母、数字、运算符、括号、空格、点号
    const allowedChars = /^[a-zA-Z0-9+\-*/%()\[\]{}\.,\s]+$/;
    return allowedChars.test(expression);
  }
}

/**
 * 时间工具
 */
export class TimeTool {
  async execute(timezone?: string, format?: string): Promise<string> {
    try {
      // 获取当前时间
      const now = new Date();
      
      // 时区处理（简化版，只支持常见时区）
      let offset = 8; // 默认上海时区 UTC+8
      if (timezone) {
        const tzMap: Record<string, number> = {
          utc: 0,
          gmt: 0,
          'asia/shanghai': 8,
          beijing: 8,
          cst: 8,
          'america/new_york': -5,
          est: -5,
          'america/los_angeles': -8,
          pst: -8,
          'europe/london': 0,
          jst: 9,
        };
        const tzLower = timezone.toLowerCase().replace(/\s+/g, '_');
        offset = tzMap[tzLower] ?? offset;
      }

      // 应用时区偏移
      const utcTime = now.getTime() + now.getTimezoneOffset() * 60000;
      const localTime = new Date(utcTime + offset * 3600000);

      // 格式化输出
      const fmt = format || 'time_chinese';
      return this.formatTime(localTime, fmt);
    } catch (error: any) {
      log.error('Time tool error:', error);
      return `错误：获取时间失败 - ${error.message || 'Unknown error'}`;
    }
  }

  private formatTime(dt: Date, format: string): string {
    const weekdayMap = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];

    switch (format) {
      case 'time_chinese': {
        const hour = dt.getHours();
        const minute = dt.getMinutes();
        return `${hour}点${minute.toString().padStart(2, '0')}分`;
      }
      case 'date_chinese': {
        const weekday = weekdayMap[dt.getDay()];
        const year = dt.getFullYear();
        const month = dt.getMonth() + 1;
        const day = dt.getDate();
        return `${year}年${month}月${day}日 ${weekday}`;
      }
      case 'iso':
        return dt.toISOString();
      case 'datetime':
        return dt.toLocaleString('zh-CN', { hour12: false });
      case 'date':
        return dt.toLocaleDateString('zh-CN');
      case 'time':
        return dt.toLocaleTimeString('zh-CN', { hour12: false });
      case 'full': {
        const weekday = weekdayMap[dt.getDay()];
        const year = dt.getFullYear();
        const month = dt.getMonth() + 1;
        const day = dt.getDate();
        const hour = dt.getHours();
        const minute = dt.getMinutes();
        const second = dt.getSeconds();
        return `${year}年${month}月${day}日 ${weekday} ${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}:${second.toString().padStart(2, '0')}`;
      }
      default: {
        const hour = dt.getHours();
        const minute = dt.getMinutes();
        return `${hour}点${minute.toString().padStart(2, '0')}分`;
      }
    }
  }
}

/**
 * 单位转换工具
 */
export class UnitConverterTool {
  private readonly conversionFactors: Record<string, Record<string, number>> = {
    length: {
      meter: 1.0,
      m: 1.0,
      kilometer: 1000.0,
      km: 1000.0,
      centimeter: 0.01,
      cm: 0.01,
      millimeter: 0.001,
      mm: 0.001,
      inch: 0.0254,
      in: 0.0254,
      foot: 0.3048,
      ft: 0.3048,
      yard: 0.9144,
      yd: 0.9144,
      mile: 1609.344,
      mi: 1609.344,
      nautical_mile: 1852.0,
      nmi: 1852.0,
    },
    weight: {
      kilogram: 1.0,
      kg: 1.0,
      gram: 0.001,
      g: 0.001,
      milligram: 0.000001,
      mg: 0.000001,
      pound: 0.453592,
      lb: 0.453592,
      ounce: 0.0283495,
      oz: 0.0283495,
      ton: 1000.0,
      metric_ton: 1000.0,
      tonne: 1000.0,
    },
    volume: {
      liter: 1.0,
      l: 1.0,
      milliliter: 0.001,
      ml: 0.001,
      gallon: 3.78541,
      gal: 3.78541,
      quart: 0.946353,
      qt: 0.946353,
      pint: 0.473176,
      pt: 0.473176,
      cup: 0.236588,
      fluid_ounce: 0.0295735,
      fl_oz: 0.0295735,
      cubic_meter: 1000.0,
      m3: 1000.0,
      cubic_centimeter: 0.001,
      cm3: 0.001,
      cc: 0.001,
    },
    area: {
      square_meter: 1.0,
      m2: 1.0,
      square_kilometer: 1000000.0,
      km2: 1000000.0,
      square_centimeter: 0.0001,
      cm2: 0.0001,
      square_millimeter: 0.000001,
      mm2: 0.000001,
      square_inch: 0.00064516,
      in2: 0.00064516,
      square_foot: 0.092903,
      ft2: 0.092903,
      square_yard: 0.836127,
      yd2: 0.836127,
      acre: 4046.86,
      hectare: 10000.0,
      ha: 10000.0,
    },
    speed: {
      meter_per_second: 1.0,
      'm/s': 1.0,
      kilometer_per_hour: 0.277778,
      'km/h': 0.277778,
      mile_per_hour: 0.44704,
      mph: 0.44704,
      foot_per_second: 0.3048,
      'ft/s': 0.3048,
      knot: 0.514444,
      kt: 0.514444,
    },
    time: {
      second: 1.0,
      s: 1.0,
      minute: 60.0,
      min: 60.0,
      hour: 3600.0,
      h: 3600.0,
      day: 86400.0,
      d: 86400.0,
      week: 604800.0,
      wk: 604800.0,
      month: 2592000.0,
      year: 31536000.0,
      yr: 31536000.0,
    },
    data: {
      byte: 1.0,
      b: 1.0,
      kilobyte: 1024.0,
      kb: 1024.0,
      megabyte: 1048576.0,
      mb: 1048576.0,
      gigabyte: 1073741824.0,
      gb: 1073741824.0,
      terabyte: 1099511627776.0,
      tb: 1099511627776.0,
      petabyte: 1125899906842624.0,
      pb: 1125899906842624.0,
    },
  };

  async execute(
    value: number,
    fromUnit: string,
    toUnit: string,
    category?: string
  ): Promise<string> {
    try {
      const from = fromUnit.toLowerCase().trim();
      const to = toUnit.toLowerCase().trim();

      // 温度转换需要特殊处理
      if (this.isTemperatureUnit(from) || this.isTemperatureUnit(to)) {
        const result = this.convertTemperature(value, from, to);
        return `${result} ${toUnit}`;
      }

      // 确定单位类别
      let cat = category?.toLowerCase().trim();
      if (!cat) {
        cat = this.detectCategory(from, to) ?? undefined;
      }

      if (!cat || !this.conversionFactors[cat]) {
        return '错误：无法识别单位类型，请指定category参数';
      }

      const factors = this.conversionFactors[cat];

      if (!factors[from]) {
        return `错误：不支持的源单位 '${fromUnit}'（类别：${cat}）`;
      }

      if (!factors[to]) {
        return `错误：不支持的目标单位 '${toUnit}'（类别：${cat}）`;
      }

      // 执行转换
      const baseValue = value * factors[from];
      const resultValue = baseValue / factors[to];

      // 格式化结果
      let resultStr: string;
      if (resultValue >= 1000) {
        resultStr = resultValue.toFixed(2);
      } else if (resultValue >= 1) {
        resultStr = resultValue.toFixed(4);
      } else {
        resultStr = resultValue.toFixed(6);
      }

      resultStr = resultStr.replace(/\.?0+$/, '');

      return `${resultStr} ${toUnit}`;
    } catch (error: any) {
      log.error('Unit converter error:', error);
      return `错误：单位转换失败 - ${error.message || 'Unknown error'}`;
    }
  }

  private isTemperatureUnit(unit: string): boolean {
    const tempUnits = ['celsius', 'c', 'fahrenheit', 'f', 'kelvin', 'k'];
    return tempUnits.includes(unit.toLowerCase());
  }

  private convertTemperature(value: number, from: string, to: string): string {
    const fromLower = from.toLowerCase();
    const toLower = to.toLowerCase();

    // 先转换为摄氏度（基准）
    let celsius: number;
    if (fromLower === 'celsius' || fromLower === 'c') {
      celsius = value;
    } else if (fromLower === 'fahrenheit' || fromLower === 'f') {
      celsius = ((value - 32) * 5) / 9;
    } else if (fromLower === 'kelvin' || fromLower === 'k') {
      celsius = value - 273.15;
    } else {
      return `错误：不支持的源温度单位 '${from}'`;
    }

    // 从摄氏度转换为目标单位
    let result: number;
    if (toLower === 'celsius' || toLower === 'c') {
      result = celsius;
    } else if (toLower === 'fahrenheit' || toLower === 'f') {
      result = (celsius * 9) / 5 + 32;
    } else if (toLower === 'kelvin' || toLower === 'k') {
      result = celsius + 273.15;
    } else {
      return `错误：不支持的目标温度单位 '${to}'`;
    }

    // 格式化结果
    let resultStr: string;
    if (Math.abs(result) >= 100) {
      resultStr = result.toFixed(2);
    } else {
      resultStr = result.toFixed(4);
    }

    return resultStr.replace(/\.?0+$/, '');
  }

  private detectCategory(from: string, to: string): string | null {
    for (const [category, factors] of Object.entries(this.conversionFactors)) {
      if (factors[from] && factors[to]) {
        return category;
      }
    }
    return null;
  }
}

/**
 * 随机数生成器工具
 */
export class RandomGeneratorTool {
  async execute(params: {
    type: string;
    min?: number;
    max?: number;
    length?: number;
    charset?: string;
    custom_chars?: string;
    choices?: string[];
    count?: number;
  }): Promise<string> {
    try {
      const { type, count = 1 } = params;
      const typeLower = type.toLowerCase().trim();

      if (count < 1) {
        return '错误：count必须大于等于1';
      }

      if (count > 100) {
        return '错误：count不能超过100（防止生成过多数据）';
      }

      let result: string;

      switch (typeLower) {
        case 'integer':
          result = this.generateInteger(params.min, params.max, count);
          break;
        case 'float':
          result = this.generateFloat(params.min, params.max, count);
          break;
        case 'string':
          result = this.generateString(params.length, params.charset, params.custom_chars, count);
          break;
        case 'choice':
          result = this.generateChoice(params.choices, count);
          break;
        case 'uuid':
          result = this.generateUuid(count);
          break;
        default:
          return `错误：不支持的生成类型 '${type}'，可选值：'integer'、'float'、'string'、'choice'、'uuid'`;
      }

      return result;
    } catch (error: any) {
      log.error('Random generator error:', error);
      return `错误：随机数生成失败 - ${error.message || 'Unknown error'}`;
    }
  }

  private generateInteger(min?: number, max?: number, count = 1): string {
    const minVal = min !== undefined ? Math.floor(min) : 0;
    const maxVal = max !== undefined ? Math.floor(max) : 100;

    if (minVal >= maxVal) {
      return `错误：min (${minVal}) 必须小于 max (${maxVal})`;
    }

    if (count === 1) {
      return String(Math.floor(Math.random() * (maxVal - minVal + 1)) + minVal);
    } else {
      const results: number[] = [];
      for (let i = 0; i < count; i++) {
        results.push(Math.floor(Math.random() * (maxVal - minVal + 1)) + minVal);
      }
      return results.join(', ');
    }
  }

  private generateFloat(min?: number, max?: number, count = 1): string {
    const minVal = min !== undefined ? min : 0.0;
    const maxVal = max !== undefined ? max : 1.0;

    if (minVal >= maxVal) {
      return `错误：min (${minVal}) 必须小于 max (${maxVal})`;
    }

    if (count === 1) {
      const result = Math.random() * (maxVal - minVal) + minVal;
      return result.toFixed(6).replace(/\.?0+$/, '');
    } else {
      const results: number[] = [];
      for (let i = 0; i < count; i++) {
        results.push(Math.random() * (maxVal - minVal) + minVal);
      }
      return results.map((r) => r.toFixed(6).replace(/\.?0+$/, '')).join(', ');
    }
  }

  private generateString(
    length?: number,
    charset?: string,
    customChars?: string,
    count = 1
  ): string {
    const len = length || 10;

    if (len < 1) {
      return '错误：length必须大于等于1';
    }

    if (len > 1000) {
      return '错误：length不能超过1000（防止生成过长字符串）';
    }

    let chars: string;
    const charsetLower = (charset || 'alphanumeric').toLowerCase().trim();

    if (charsetLower === 'custom') {
      if (!customChars) {
        return '错误：使用custom字符集时必须提供custom_chars参数';
      }
      chars = customChars;
    } else if (charsetLower === 'alphanumeric') {
      chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    } else if (charsetLower === 'letters') {
      chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
    } else if (charsetLower === 'digits') {
      chars = '0123456789';
    } else if (charsetLower === 'hex') {
      chars = '0123456789abcdef';
    } else {
      return `错误：不支持的字符集类型 '${charset}'，可选值：'alphanumeric'、'letters'、'digits'、'hex'、'custom'`;
    }

    if (!chars) {
      return '错误：字符集不能为空';
    }

    const generateOne = (): string => {
      let result = '';
      for (let i = 0; i < len; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
      }
      return result;
    };

    if (count === 1) {
      return generateOne();
    } else {
      const results: string[] = [];
      for (let i = 0; i < count; i++) {
        results.push(generateOne());
      }
      return results.join(', ');
    }
  }

  private generateChoice(choices?: string[], count = 1): string {
    if (!choices || !Array.isArray(choices)) {
      return '错误：使用choice类型时必须提供choices参数（数组）';
    }

    if (choices.length === 0) {
      return '错误：choices列表不能为空';
    }

    if (count === 1) {
      return String(choices[Math.floor(Math.random() * choices.length)]);
    } else {
      const results: string[] = [];
      for (let i = 0; i < count; i++) {
        results.push(String(choices[Math.floor(Math.random() * choices.length)]));
      }
      return results.join(', ');
    }
  }

  private generateUuid(count = 1): string {
    const generateOne = (): string => {
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        const v = c === 'x' ? r : (r & 0x3) | 0x8;
        return v.toString(16);
      });
    };

    if (count === 1) {
      return generateOne();
    } else {
      const results: string[] = [];
      for (let i = 0; i < count; i++) {
        results.push(generateOne());
      }
      return results.join(', ');
    }
  }
}

/**
 * 高德地图天气工具
 */
export class AmapWeatherTool {
  private apiKey: string;

  constructor(apiKey?: string) {
    // 从环境变量获取 API key
    this.apiKey = apiKey || import.meta.env.VITE_AMAP_MAPS_API_KEY || '';
    if (!this.apiKey) {
      log.warn('高德地图 API key 未配置，请设置 VITE_AMAP_MAPS_API_KEY 环境变量');
    }
  }

  async execute(city: string): Promise<string> {
    if (!this.apiKey) {
      return '错误：高德地图 API key 未配置';
    }

    try {
      const url = 'https://restapi.amap.com/v3/weather/weatherInfo';
      const params = new URLSearchParams({
        key: this.apiKey,
        city: city,
        extensions: 'all',
      });

      log.debug(`查询高德天气: ${city}`);

      const response = await fetch(`${url}?${params.toString()}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.status !== '1') {
        const errorMsg = data.info || data.infocode || 'Unknown error';
        return `错误：${errorMsg}`;
      }

      const forecasts = data.forecasts;
      if (!forecasts || forecasts.length === 0) {
        return '错误：没有可用的预报数据';
      }

      const result = {
        city: forecasts[0].city,
        forecasts: forecasts[0].casts,
      };

      log.debug(`高德天气查询成功: ${city}`, result);
      return JSON.stringify(result, null, 2);
    } catch (error: any) {
      log.error('高德天气查询失败:', error);
      return `错误：获取天气失败 - ${error.message || 'Unknown error'}`;
    }
  }
}

/**
 * Tavily 搜索工具
 */
export class TavilySearchTool {
  private apiKey: string;

  constructor(apiKey?: string) {
    // 从环境变量获取 API key
    this.apiKey = apiKey || import.meta.env.VITE_TAVILY_API_KEY || '';
    if (!this.apiKey) {
      log.warn('Tavily API key 未配置，请设置 VITE_TAVILY_API_KEY 环境变量');
    }
  }

  async execute(query: string, searchDepth: string = 'basic'): Promise<string> {
    if (!this.apiKey) {
      return '错误：Tavily API key 未配置';
    }

    if (!query || !query.trim()) {
      return '错误：搜索查询不能为空';
    }

    try {
      const url = 'https://api.tavily.com/search';
      
      log.debug(`Tavily 搜索: ${query}`, { searchDepth });

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          api_key: this.apiKey,
          query: query.trim(),
          search_depth: searchDepth,
          topic: 'general',
          country: 'china',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          `HTTP ${response.status}: ${errorData.error || response.statusText}`
        );
      }

      const data = await response.json();

      // 格式化返回结果
      return this.formatSearchResults(data, query);
    } catch (error: any) {
      log.error('Tavily 搜索失败:', error);
      return `错误：Tavily搜索执行失败 - ${error.message || 'Unknown error'}`;
    }
  }

  private formatSearchResults(data: any, query: string): string {
    const resultParts: string[] = [];

    // 添加查询信息
    resultParts.push(`🔍 搜索查询: ${query}`);
    resultParts.push('');

    // 添加答案（如果有）
    if (data.answer) {
      resultParts.push('📝 答案:');
      resultParts.push(data.answer);
      resultParts.push('');
    }

    // 添加搜索结果
    const results = data.results || [];
    if (results.length > 0) {
      resultParts.push(`📚 相关结果 (${results.length} 条):`);
      resultParts.push('');

      // 最多显示5条结果
      const displayResults = results.slice(0, 5);
      displayResults.forEach((item: any, index: number) => {
        const title = item.title || '无标题';
        const url = item.url || '';
        let content = item.content || '';
        const score = item.score;

        // 限制内容长度，避免过长
        if (content.length > 200) {
          content = content.substring(0, 200) + '...';
        }

        resultParts.push(`${index + 1}. ${title}`);
        if (url) {
          resultParts.push(`   🔗 ${url}`);
        }
        if (content) {
          resultParts.push(`   📄 ${content}`);
        }
        if (score !== undefined && score !== null) {
          resultParts.push(`   ⭐ 相关度: ${score.toFixed(2)}`);
        }
        resultParts.push('');
      });
    }

    // 添加响应时间（如果有）
    if (data.response_time !== undefined && data.response_time !== null) {
      resultParts.push(`⏱️ 响应时间: ${data.response_time.toFixed(2)}秒`);
    }

    return resultParts.join('\n');
  }
}

/**
 * 前端可执行的工具列表
 * 
 * 这些工具可以在前端直接执行。
 * 
 * 注意：
 * - weather 工具需要 OpenWeatherMap API key，因此不在前端执行，通过后端 API 执行
 * - text_summarizer 工具需要调用 LLM，因此不在前端执行，通过后端 API 执行
 * - amap_weather 工具需要高德地图 API key，但可以在前端执行（从环境变量读取）
 * - tavily_search 工具需要 Tavily API key，可以在前端执行（从环境变量读取）
 * - 其他 amap_* 工具需要高德地图 API key，通过后端 API 执行
 */
export const FRONTEND_EXECUTABLE_TOOLS = [
  'calculator',
  'time',
  'unit_converter',
  'random_generator',
  'amap_weather',
  'tavily_search',
];

/**
 * 工具实例映射
 */
export const toolInstances: Record<string, any> = {
  calculator: new CalculatorTool(),
  time: new TimeTool(),
  unit_converter: new UnitConverterTool(),
  random_generator: new RandomGeneratorTool(),
  amap_weather: new AmapWeatherTool(),
  tavily_search: new TavilySearchTool(),
};

/**
 * 在前端执行工具
 * 
 * @param toolName - 工具名称
 * @param parameters - 工具参数
 * @returns 执行结果
 */
export async function executeFrontendTool(
  toolName: string,
  parameters: Record<string, any>
): Promise<string> {
  const tool = toolInstances[toolName];
  if (!tool) {
    throw new Error(`工具 ${toolName} 不在前端可执行列表中`);
  }

  log.debug(`前端执行工具: ${toolName}`, parameters);

  try {
    let result: string;

    switch (toolName) {
      case 'calculator':
        result = await (tool as CalculatorTool).execute(parameters.expression);
        break;
      case 'time':
        result = await (tool as TimeTool).execute(parameters.timezone, parameters.format);
        break;
      case 'unit_converter':
        result = await (tool as UnitConverterTool).execute(
          parameters.value,
          parameters.from_unit,
          parameters.to_unit,
          parameters.category
        );
        break;
      case 'random_generator':
        // 确保 parameters 包含必需的 type 属性
        if (!parameters.type) {
          throw new Error('random_generator 工具需要 type 参数');
        }
        result = await (tool as RandomGeneratorTool).execute({
          type: parameters.type,
          min: parameters.min,
          max: parameters.max,
          length: parameters.length,
          charset: parameters.charset,
          custom_chars: parameters.custom_chars,
          choices: parameters.choices,
          count: parameters.count,
        });
        break;
      case 'amap_weather':
        if (!parameters.city) {
          throw new Error('amap_weather 工具需要 city 参数');
        }
        result = await (tool as AmapWeatherTool).execute(parameters.city);
        break;
      case 'tavily_search':
        if (!parameters.query) {
          throw new Error('tavily_search 工具需要 query 参数');
        }
        result = await (tool as TavilySearchTool).execute(
          parameters.query,
          parameters.search_depth || 'basic'
        );
        break;
      default:
        throw new Error(`未实现的工具: ${toolName}`);
    }

    log.debug(`工具执行成功: ${toolName}`, result);
    return result;
  } catch (error: any) {
    log.error(`工具执行失败: ${toolName}`, error);
    throw error;
  }
}

/**
 * 前端内置工具定义
 * 
 * 返回所有前端内置工具的定义（name, description, parameters）
 */
export function getFrontendToolDefinitions() {
  return [
    {
      name: 'calculator',
      description: '执行数学计算，支持基本运算（加减乘除、取模、幂运算）和科学计算（三角函数、对数、指数等）',
      parameters: {
        type: 'object',
        properties: {
          expression: {
            type: 'string',
            description: '要计算的数学表达式，例如：2+2, sin(pi/2), sqrt(16)',
          },
        },
        required: ['expression'],
      },
    },
    {
      name: 'time',
      description: '获取当前时间和日期，支持多种时区和格式',
      parameters: {
        type: 'object',
        properties: {
          timezone: {
            type: 'string',
            description: '时区，例如：Asia/Shanghai, America/New_York, UTC',
          },
          format: {
            type: 'string',
            description: '时间格式：chinese（中文）、iso（ISO 8601）、full（完整格式）',
            enum: ['chinese', 'iso', 'full'],
          },
        },
        required: [],
      },
    },
    {
      name: 'unit_converter',
      description: '单位转换工具，支持长度、重量、体积、面积、速度、时间、数据存储和温度转换',
      parameters: {
        type: 'object',
        properties: {
          value: {
            type: 'number',
            description: '要转换的数值',
          },
          from_unit: {
            type: 'string',
            description: '源单位，例如：km, kg, celsius',
          },
          to_unit: {
            type: 'string',
            description: '目标单位，例如：m, g, fahrenheit',
          },
          category: {
            type: 'string',
            description: '单位类别（可选）：length, weight, volume, area, speed, time, data, temperature',
            enum: ['length', 'weight', 'volume', 'area', 'speed', 'time', 'data', 'temperature'],
          },
        },
        required: ['value', 'from_unit', 'to_unit'],
      },
    },
    {
      name: 'random_generator',
      description: '生成随机数、随机字符串、随机选择或UUID',
      parameters: {
        type: 'object',
        properties: {
          type: {
            type: 'string',
            description: '生成类型',
            enum: ['integer', 'float', 'string', 'choice', 'uuid'],
          },
          min: {
            type: 'number',
            description: '最小值（仅用于 integer 和 float）',
          },
          max: {
            type: 'number',
            description: '最大值（仅用于 integer 和 float）',
          },
          length: {
            type: 'number',
            description: '字符串长度（仅用于 string）',
          },
          charset: {
            type: 'string',
            description: '字符集（仅用于 string）：alphanumeric, numeric, lowercase, uppercase, mixed',
            enum: ['alphanumeric', 'numeric', 'lowercase', 'uppercase', 'mixed'],
          },
          choices: {
            type: 'array',
            items: { type: 'string' },
            description: '选择列表（仅用于 choice）',
          },
          count: {
            type: 'number',
            description: '生成数量（批量生成）',
          },
        },
        required: ['type'],
      },
    },
    {
      name: 'amap_weather',
      description: '查询高德地图天气信息，需要配置 VITE_AMAP_MAPS_API_KEY 环境变量',
      parameters: {
        type: 'object',
        properties: {
          city: {
            type: 'string',
            description: '城市名称或adcode，例如：北京、上海、110000',
          },
        },
        required: ['city'],
      },
    },
    {
      name: 'tavily_search',
      description: '使用 Tavily 进行网络搜索，需要配置 VITE_TAVILY_API_KEY 环境变量',
      parameters: {
        type: 'object',
        properties: {
          query: {
            type: 'string',
            description: '搜索查询',
          },
          search_depth: {
            type: 'string',
            description: '搜索深度：basic（基础）或 advanced（高级）',
            enum: ['basic', 'advanced'],
            default: 'basic',
          },
        },
        required: ['query'],
      },
    },
  ];
}

