import { useEffect, useState, useRef } from 'react'

export default function LogTable() {
  const [logs, setLogs] = useState([])
  const [currentPage, setCurrentPage] = useState(1)
  const [pageInput, setPageInput] = useState('1')
  const [dslQuery, setDslQuery] = useState('')
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [logsPerPage, setLogsPerPage] = useState(20)
  const [pageError, setPageError] = useState(false)
  const intervalRef = useRef(null)

  useEffect(() => {
    fetchLogs()
  }, [])

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchLogs, 1000)
    } else {
      clearInterval(intervalRef.current)
    }
    return () => clearInterval(intervalRef.current)
  }, [autoRefresh, dslQuery])

  useEffect(() => {
    setPageInput(currentPage.toString())
  }, [currentPage])

  function fetchLogs() {
    const base = 'http://localhost:8000/ritual/logs'
    const url = dslQuery.trim()
      ? `${base}/dsl?q=${encodeURIComponent(dslQuery)}`
      : base

    fetch(url)
      .then(res => res.json())
      .then(data => {
        setLogs(data)
        setCurrentPage(1)
      })
      .catch(err => console.error('Ошибка загрузки логов:', err))
  }

  const totalPages = Math.max(1, Math.ceil(logs.length / logsPerPage))
  const indexOfLastLog = currentPage * logsPerPage
  const indexOfFirstLog = indexOfLastLog - logsPerPage
  const currentLogs = logs.slice(indexOfFirstLog, indexOfLastLog)

  function getRowStyle(level) {
    switch (level) {
      case 'CRITICAL': return 'text-red-400'
      case 'ERROR':    return 'text-red-500'
      case 'WARN':
      case 'WARNING':  return 'text-yellow-400'
      case 'INFO':     return 'text-emerald-400'
      case 'DEBUG':    return 'text-gray-500'
      default:         return 'text-white'
    }
  }

  function handlePageInputChange(e) {
    const value = e.target.value
    setPageInput(value)

    const num = parseInt(value)
    if (!isNaN(num) && num >= 1 && num <= totalPages) {
      setPageError(false)
    } else {
      setPageError(true)
    }
  }

  function goToInputPage() {
    const num = parseInt(pageInput)
    if (!isNaN(num) && num >= 1 && num <= totalPages) {
      setCurrentPage(num)
      setPageError(false)
    } else {
      setPageError(true)
    }
  }

  return (
      <div className="bg-black min-h-screen p-4">

        {/* ЛОГО */}
        <div className="flex justify-center mb-4">
          <img src="/src/assets/gritana-logo.png" alt="GRITANA Logo" className="h-24 object-contain"/>
        </div>

        {/* ФИЛЬТРЫ + КНОПКИ */}
        <div className="mb-6 flex justify-center">
          <div className="flex gap-2 items-center">
            <input
                type="text"
                value={dslQuery}
                onChange={e => setDslQuery(e.target.value)}
                placeholder="Пример: level:ERROR AND module:main.py"
                className="px-4 py-2 w-[500px] bg-zinc-900 text-green-400 border border-gray-700 font-mono text-sm placeholder:text-gray-600 focus:outline-none focus:ring focus:ring-green-600"
            />
            <button
                onClick={fetchLogs}
                className="px-4 py-2 bg-green-800 hover:bg-green-700 text-white font-mono text-sm"
            >
              🔍 Фильтровать
            </button>
            <button
                onClick={() => setAutoRefresh(prev => !prev)}
                className={`px-4 py-2 font-mono text-sm border ${
                    autoRefresh
                        ? 'bg-red-900 text-white border-red-600 hover:bg-red-800'
                        : 'bg-zinc-800 text-gray-400 border-gray-600 hover:bg-zinc-700'
                }`}
            >
              {autoRefresh ? '⏸ Автообновление' : '▶️ Автообновлять'}
            </button>
          </div>
        </div>

        {/* ТАБЛИЦА */}
        <div
            className="grid grid-cols-[200px_100px_150px_150px_250px_100px_300px_1fr_1fr] text-sm font-mono text-green-300 border border-gray-700 bg-zinc-950 rounded mx-auto w-fit">
          <div
              className="col-span-9 grid grid-cols-[200px_100px_150px_150px_250px_100px_300px_1fr_1fr] bg-zinc-800 font-bold border-b border-gray-700 text-left">
            <div className="p-2 border-r border-gray-700 text-center">Время</div>
            <div className="p-2 border-r border-gray-700 text-center">Уровень</div>
            <div className="p-2 border-r border-gray-700">Источник</div>
            <div className="p-2 border-r border-gray-700">Процесс</div>
            <div className="p-2 border-r border-gray-700">Модуль</div>
            <div className="p-2 border-r border-gray-700">Версия</div>
            <div className="p-2 border-r border-gray-700">Запуск (event_run_id)</div>
            <div className="p-2 border-r border-gray-700">Сообщение</div>
            <div className="p-2">Traceback / Context</div>
          </div>

          {currentLogs.map(log => {
            const rowStyle = getRowStyle(log.level)
            return (
                <div key={log.id} className="contents">
                  <div className={`p-2 border-t border-gray-700 text-center ${rowStyle}`}>
                    {new Date(log.timestamp).toLocaleString()}
                  </div>
                  <div className={`p-2 border-t border-gray-700 text-center ${rowStyle}`}>{log.level}</div>
                  <div className={`p-2 border-t border-gray-700 ${rowStyle}`}>{log.source ||
                      <span className="text-gray-600 italic">—</span>}</div>
                  <div className={`p-2 border-t border-gray-700 ${rowStyle}`}>{log.process ||
                      <span className="text-gray-600 italic">—</span>}</div>
                  <div className={`p-2 border-t border-gray-700 ${rowStyle}`}>{log.module}</div>
                  <div className={`p-2 border-t border-gray-700 ${rowStyle}`}>{log.version ||
                      <span className="text-gray-600 italic">—</span>}</div>
                  <div className={`p-2 border-t border-gray-700 text-xs break-all ${rowStyle}`}>{log.event_run_id ||
                      <span className="text-gray-600 italic">—</span>}</div>
                  <div className={`p-2 border-t border-gray-700 whitespace-pre-wrap ${rowStyle}`}>{log.message}</div>
                  <div className={`p-2 border-t border-gray-700 ${rowStyle}`}>
                    {log.traceback || log.context ? (
                        <details className="whitespace-pre-wrap">
                          <summary className="cursor-pointer text-red-300 hover:text-red-200">Подробнее</summary>
                          {log.traceback && <pre className="text-red-400">{log.traceback}</pre>}
                          {log.context && <pre className="text-gray-400">{JSON.stringify(log.context, null, 2)}</pre>}
                        </details>
                    ) : (
                        <span className="text-gray-600 italic">—</span>
                    )}
                  </div>
                </div>
            )
          })}
        </div>


        {/* ПАГИНАЦИЯ */}
        <div className="flex justify-center items-center gap-4 mt-6 font-mono text-sm text-gray-400">
          <button
              className="px-4 py-1 border border-gray-700 hover:bg-zinc-800 disabled:opacity-30"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(prev => prev - 1)}
          >
            ← Назад
          </button>


          <div className="flex items-center gap-1">
            <span>1 ...</span>
            <input
                type="text"
                value={pageInput}
                onChange={handlePageInputChange}
                onBlur={goToInputPage}
                onKeyDown={(e) => e.key === 'Enter' && goToInputPage()}
                className={`w-12 text-center border px-2 py-1 outline-none bg-black ${
                    pageError ? 'border-red-500 text-red-400' : 'border-gray-700 text-green-400'
                }`}
            />
            <span>... {totalPages}</span>
          </div>

          <button
              className="px-4 py-1 border border-gray-700 hover:bg-zinc-800 disabled:opacity-30"
              disabled={currentPage === totalPages || totalPages === 0}
              onClick={() => setCurrentPage(prev => prev + 1)}
          >
            Вперёд →
          </button>

          <select
              value={logsPerPage}
              onChange={e => {
                setLogsPerPage(parseInt(e.target.value))
                setCurrentPage(1)
              }}
              className="ml-4 px-2 py-1 bg-black border border-gray-700 text-green-300 font-mono text-sm"
          >
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>

        </div>
      </div>
  )
}
