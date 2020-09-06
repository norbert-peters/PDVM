import React from 'react'
import { PdvmBox } from '../pdvmComponents/PdvmBox'
import { PdvmIconButton } from '../pdvmComponents/PdvmIconButton'

export const PdvmHeader = (props) => {
  return (
    <PdvmBox component="span" display="flex"  >
        {<props.phType>{props.phTitle}</props.phType>}
        <PdvmBox p={1} >
            {props.phExcerpt && props.phButton && (
            <>
                {Object.keys(props.phButton).map((value, key) => 
                    (
                      <div key = {props.phButton[key].id}>
                        <PdvmIconButton 
                            ttitle = {props.phButton[key].ttitle}
                            togo = {props.phButton[key].togo} 
                            nicon = {props.phButton[key].nicon} 
                        />
                      </div>
                    )
                  )
                }
            </>
            )}    
        </PdvmBox>
    </PdvmBox> 
  )
}